import base64
import io
import logging
import os

try:
    import trimesh
except ImportError:
    trimesh = None
    logging.getLogger(__name__).debug(
        "trimesh not installed; 3D conversion unavailable"
    )

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.exception import FailedJobError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    model_3d = fields.Binary(
        string="3D Model",
        attachment=True,
        help="Upload a 3D model file (GLB/GLTF or auto-converted from STL/OBJ/STEP).",
    )
    model_3d_source = fields.Binary(
        string="3D Source File",
        attachment=True,
    )
    model_3d_source_filename = fields.Char(
        string="Source Filename",
    )
    model_3d_filename = fields.Char(
        string="3D Model Filename",
        compute="_compute_model_3d_filename",
        store=True,
        readonly=True,
    )
    model_3d_conversion_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        default="draft",
        readonly=True,
        string="Conversion State",
    )
    model_3d_conversion_error = fields.Text(
        string="Conversion Error",
        readonly=True,
    )
    model_3d_job_uuid = fields.Char(
        string="Job UUID",
        readonly=True,
    )
    model_3d_source_size_kb = fields.Integer(
        string="Source Size (KB)",
        compute="_compute_model_3d_source_size_kb",
        store=True,
        readonly=True,
    )

    @api.depends("model_3d_source")
    def _compute_model_3d_source_size_kb(self):
        for record in self:
            source = record.with_context(bin_size=False).model_3d_source
            if source:
                raw = base64.b64decode(source)
                record.model_3d_source_size_kb = len(raw) // 1024
            else:
                record.model_3d_source_size_kb = 0

    @api.onchange("model_3d_source")
    def _onchange_model_3d_source(self):
        for record in self:
            record.model_3d = False
            record.model_3d_conversion_state = "draft"
            record.model_3d_conversion_error = False
            record.model_3d_job_uuid = False

    @api.depends("model_3d_source_filename")
    def _compute_model_3d_filename(self):
        for record in self:
            if record.model_3d_source_filename:
                name, _ext = os.path.splitext(record.model_3d_source_filename)
                record.model_3d_filename = name + ".glb"
            else:
                record.model_3d_filename = False

    def _cancel_model_3d_job(self):
        if self.model_3d_job_uuid:
            job = (
                self.env["queue.job"]
                .sudo()
                .search([("uuid", "=", self.model_3d_job_uuid)], limit=1)
            )
            if job and job.state not in ("done", "failed", "cancelled"):
                job.button_cancelled()

    def action_model_3d_abort(self):
        self.ensure_one()
        self._cancel_model_3d_job()
        self.write(
            {
                "model_3d_conversion_state": "draft",
                "model_3d_job_uuid": False,
                "model_3d_conversion_error": False,
            }
        )

    def action_model_3d_clear(self):
        self.ensure_one()
        self._cancel_model_3d_job()
        self.write(
            {
                "model_3d_source": False,
                "model_3d_source_filename": False,
                "model_3d": False,
                "model_3d_filename": False,
                "model_3d_conversion_state": "draft",
                "model_3d_conversion_error": False,
                "model_3d_job_uuid": False,
            }
        )

    def action_model_3d_convert(self):
        self.ensure_one()
        if self.model_3d_conversion_state in ("queued", "processing"):
            self.action_model_3d_abort()

        if not self.model_3d_source:
            raise UserError(_("No source file uploaded."))

        max_size_kb = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("model_3d_convert.max.size.kb", default=51200)
        )
        if self.model_3d_source_size_kb > max_size_kb:
            raise UserError(
                _(
                    "File size %(size)d KB exceeds the maximum allowed"
                    " size of %(max_size)d KB."
                )
                % {"size": self.model_3d_source_size_kb, "max_size": max_size_kb}
            )

        ext = (
            os.path.splitext(self.model_3d_source_filename or "")[1].lstrip(".").lower()
        )

        if ext in ("glb", "gltf"):
            self.write(
                {
                    "model_3d": self.model_3d_source,
                    "model_3d_filename": self.model_3d_filename,
                    "model_3d_conversion_state": "done",
                }
            )
        else:
            self.write(
                {
                    "model_3d_conversion_state": "queued",
                    "model_3d_conversion_error": False,
                }
            )
            job = self.with_delay(
                channel="root.model_3d_conversion",
                max_retries=0,
            ).model_3d_run_conversion()
            self.write({"model_3d_job_uuid": job.uuid})

    def model_3d_run_conversion(self):
        self.write({"model_3d_conversion_state": "processing"})
        try:
            if trimesh is None:
                raise ImportError(
                    "trimesh is not installed. " "Run: pip install trimesh cascadio"
                )
            ext = (
                os.path.splitext(self.model_3d_source_filename or "")[1]
                .lstrip(".")
                .lower()
                or "stl"
            )
            source_bytes = base64.b64decode(self.model_3d_source, validate=False)
            mesh = trimesh.load(io.BytesIO(source_bytes), file_type=ext)
            glb_bytes = mesh.export(file_type="glb")
            glb_b64 = base64.b64encode(glb_bytes).decode()
            self.write(
                {
                    "model_3d": glb_b64,
                    "model_3d_filename": self.model_3d_filename,
                    "model_3d_conversion_state": "done",
                    "model_3d_conversion_error": False,
                }
            )
        except Exception as exc:
            with self.pool.cursor() as cr:
                self.with_env(self.env(cr=cr)).write(
                    {
                        "model_3d_conversion_state": "failed",
                        "model_3d_conversion_error": str(exc),
                    }
                )
            raise FailedJobError(str(exc)) from exc

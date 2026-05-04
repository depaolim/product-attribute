from odoo.tests import TransactionCase

from ..common import VALID_GLB_B64, _make_source


class TestAbortAndClear(TransactionCase):
    def _create_stl_template(self):
        return self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": _make_source(1),
                "model_3d_source_filename": "part.stl",
            }
        )

    def _queued_template(self):
        template = self._create_stl_template()
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "queued")
        return template

    # --- action_model_3d_abort ---

    def test_abort_resets_state_to_draft(self):
        template = self._queued_template()
        template.action_model_3d_abort()
        self.assertEqual(template.model_3d_conversion_state, "draft")

    def test_abort_clears_job_uuid(self):
        template = self._queued_template()
        template.action_model_3d_abort()
        self.assertFalse(template.model_3d_job_uuid)

    def test_abort_clears_conversion_error(self):
        template = self._create_stl_template()
        template.write(
            {
                "model_3d_conversion_state": "failed",
                "model_3d_conversion_error": "boom",
                "model_3d_job_uuid": "some-uuid",
            }
        )
        template.action_model_3d_abort()
        self.assertFalse(template.model_3d_conversion_error)

    def test_abort_cancels_pending_queue_job(self):
        template = self._queued_template()
        job_uuid = template.model_3d_job_uuid
        template.action_model_3d_abort()
        job = self.env["queue.job"].search([("uuid", "=", job_uuid)])
        self.assertEqual(job.state, "cancelled")

    def test_abort_safe_when_no_job_uuid(self):
        template = self._create_stl_template()
        self.assertFalse(template.model_3d_job_uuid)
        try:
            template.action_model_3d_abort()
        except Exception:
            self.fail("action_model_3d_abort raised unexpectedly with no job UUID")
        self.assertEqual(template.model_3d_conversion_state, "draft")

    # --- action_model_3d_clear ---

    def test_clear_removes_source(self):
        template = self._create_stl_template()
        template.action_model_3d_clear()
        self.assertFalse(template.model_3d_source)

    def test_clear_removes_source_filename(self):
        template = self._create_stl_template()
        template.action_model_3d_clear()
        self.assertFalse(template.model_3d_source_filename)

    def test_clear_removes_model_3d(self):
        template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": VALID_GLB_B64,
                "model_3d_source_filename": "part.glb",
            }
        )
        template.action_model_3d_convert()
        self.assertTrue(template.model_3d)
        template.action_model_3d_clear()
        self.assertFalse(template.model_3d)

    def test_clear_resets_state_to_draft(self):
        template = self._create_stl_template()
        template.write({"model_3d_conversion_state": "failed"})
        template.action_model_3d_clear()
        self.assertEqual(template.model_3d_conversion_state, "draft")

    def test_clear_cancels_pending_queue_job(self):
        template = self._queued_template()
        job_uuid = template.model_3d_job_uuid
        template.action_model_3d_clear()
        job = self.env["queue.job"].search([("uuid", "=", job_uuid)])
        self.assertEqual(job.state, "cancelled")

    def test_clear_safe_when_no_source(self):
        template = self.env["product.template"].create({"name": "Empty Product"})
        try:
            template.action_model_3d_clear()
        except Exception:
            self.fail("action_model_3d_clear raised unexpectedly on an empty record")

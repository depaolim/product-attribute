import base64

from odoo.fields import Binary
from odoo.tests import TransactionCase

from ..common import _make_source


class TestModelFields(TransactionCase):
    def test_fields_exist(self):
        fields = self.env["product.template"]._fields
        for field_name in [
            "model_3d",
            "model_3d_source",
            "model_3d_source_filename",
            "model_3d_filename",
            "model_3d_conversion_state",
            "model_3d_conversion_error",
            "model_3d_job_uuid",
            "model_3d_source_size_kb",
        ]:
            self.assertIn(
                field_name,
                fields,
                f"Field {field_name} must exist on product.template",
            )

    def test_model_3d_is_binary_with_attachment(self):
        field = self.env["product.template"]._fields["model_3d"]
        self.assertIsInstance(field, Binary)
        self.assertTrue(field.attachment)

    def test_model_3d_source_is_binary_with_attachment(self):
        field = self.env["product.template"]._fields["model_3d_source"]
        self.assertIsInstance(field, Binary)
        self.assertTrue(field.attachment)

    def test_default_state_is_draft(self):
        template = self.env["product.template"].create({"name": "Test Product"})
        self.assertEqual(template.model_3d_conversion_state, "draft")

    def test_file_size_computed_on_upload(self):
        raw_bytes = b"x" * 2048
        b64 = base64.b64encode(raw_bytes).decode()
        template = self.env["product.template"].create(
            {"name": "Test Product", "model_3d_source": b64}
        )
        self.assertEqual(template.model_3d_source_size_kb, len(raw_bytes) // 1024)

    def test_file_size_zero_when_no_file(self):
        template = self.env["product.template"].create({"name": "Test Product"})
        self.assertEqual(template.model_3d_source_size_kb, 0)

    def test_model_3d_filename_derived_from_source_filename(self):
        template = self.env["product.template"].create(
            {"name": "Test Product", "model_3d_source_filename": "bracket.stl"}
        )
        self.assertEqual(template.model_3d_filename, "bracket.glb")

    def test_model_3d_filename_derived_from_obj_source(self):
        template = self.env["product.template"].create(
            {"name": "Test Product", "model_3d_source_filename": "bracket.obj"}
        )
        self.assertEqual(template.model_3d_filename, "bracket.glb")

    def test_model_3d_filename_false_when_no_source_filename(self):
        template = self.env["product.template"].create({"name": "Test Product"})
        self.assertFalse(template.model_3d_filename)

    def test_model_3d_filename_handles_no_extension(self):
        template = self.env["product.template"].create(
            {"name": "Test Product", "model_3d_source_filename": "bracket"}
        )
        self.assertEqual(template.model_3d_filename, "bracket.glb")

    def test_onchange_source_resets_transient_fields(self):
        template = self.env["product.template"].create({"name": "Test Product"})
        template.write(
            {
                "model_3d": _make_source(1),
                "model_3d_conversion_state": "done",
                "model_3d_conversion_error": "some error",
                "model_3d_job_uuid": "some-uuid",
            }
        )
        template._onchange_model_3d_source()
        self.assertFalse(template.model_3d)
        self.assertEqual(template.model_3d_conversion_state, "draft")
        self.assertFalse(template.model_3d_conversion_error)
        self.assertFalse(template.model_3d_job_uuid)

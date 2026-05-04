from lxml import etree

from odoo.tests import TransactionCase


class TestViewIntegration(TransactionCase):
    def _get_arch(self):
        view = self.env.ref("product_model_3d.product_template_view_form_inherit")
        return etree.fromstring(view.arch)

    def test_view_loads_without_error(self):
        Form = self.env["product.template"]
        view_id = self.env.ref("product_model_3d.product_template_view_form_inherit").id
        result = Form.get_view(view_id, "form")
        self.assertIn("arch", result)
        arch = result["arch"]
        self.assertIn("model_3d_source_upload", arch)

    def test_model_3d_uses_model_viewer_3d_widget(self):
        arch = self._get_arch()
        fields = arch.xpath("//field[@name='model_3d']")
        self.assertTrue(fields, "model_3d field must be present in arch")
        self.assertEqual(fields[0].get("widget"), "model_viewer_3d")

    def test_model_3d_raw_binary_widget_not_present(self):
        arch = self._get_arch()
        fields = arch.xpath("//field[@name='model_3d']")
        for field in fields:
            self.assertNotEqual(
                field.get("widget"),
                "binary",
                "model_3d must not use the binary widget",
            )

    def test_convert_button_not_in_header(self):
        arch = self._get_arch()
        buttons = arch.xpath("//header//button[@name='action_model_3d_convert']")
        self.assertFalse(
            buttons,
            "action_model_3d_convert button must not appear inside <header>",
        )

    def test_3d_model_page_present(self):
        arch = self._get_arch()
        pages = arch.xpath("//page[@string='3D Model']")
        self.assertTrue(pages, "<page string='3D Model'> must exist in the view")

    def test_model_3d_source_uses_upload_widget(self):
        arch = self._get_arch()
        fields = arch.xpath("//field[@name='model_3d_source']")
        self.assertTrue(fields, "model_3d_source field must be present in arch")
        self.assertEqual(fields[0].get("widget"), "model_3d_source_upload")

    def test_view_loads_cleanly_with_empty_model_3d(self):
        template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_conversion_state": "draft",
                "model_3d": False,
            }
        )
        view_id = self.env.ref("product_model_3d.product_template_view_form_inherit").id
        result = template.get_view(view_id, "form")
        self.assertIn("arch", result)

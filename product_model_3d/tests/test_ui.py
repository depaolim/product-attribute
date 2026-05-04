import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestJsUnit(odoo.tests.HttpCase):
    """Run this module's Hoot unit tests in a headless browser."""

    def test_js_unit(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=30000"
            "&filter=@product_model_3d",
            "",
            "",
            login="admin",
            timeout=300,
            success_signal="[HOOT] Test suite succeeded",
        )

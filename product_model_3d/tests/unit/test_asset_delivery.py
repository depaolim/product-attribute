from odoo.tests import TransactionCase

from ..common import MODULE_ROOT, _load_manifest


class TestAssetDelivery(TransactionCase):
    def _backend_assets(self):
        manifest = _load_manifest()
        return manifest.get("assets", {}).get("web.assets_backend", [])

    def test_model_viewer_widget_js_in_asset_bundle(self):
        self.assertTrue(
            any("model_viewer_widget.esm.js" in str(e) for e in self._backend_assets()),
            "model_viewer_widget.esm.js not found in web.assets_backend bundle",
        )

    def test_model_3d_source_upload_widget_js_in_asset_bundle(self):
        self.assertTrue(
            any(
                "model_3d_source_upload_widget.esm.js" in str(e)
                for e in self._backend_assets()
            ),
            "model_3d_source_upload_widget.esm.js not in web.assets_backend",
        )

    def test_model_viewer_js_loaded_dynamically(self):
        """model-viewer is an ES module; it must be injected at runtime, not bundled."""
        js_path = MODULE_ROOT / "static" / "src" / "js" / "model_viewer_widget.esm.js"
        self.assertIn(
            "model-viewer.min.js",
            js_path.read_text(),
            "model-viewer.min.js not referenced in model_viewer_widget.esm.js",
        )

    def test_model_viewer_js_file_exists(self):
        js_path = MODULE_ROOT / "static" / "lib" / "model-viewer.min.js"
        self.assertTrue(js_path.exists(), f"File not found: {js_path}")

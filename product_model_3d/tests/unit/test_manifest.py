from odoo.tests import TransactionCase

from ..common import _load_manifest


class TestManifest(TransactionCase):
    def test_required_keys_present(self):
        manifest = _load_manifest()
        for key in ("name", "version", "license", "depends"):
            self.assertIn(key, manifest, f"Manifest missing key: {key}")

    def test_version_matches_odoo18_pattern(self):
        manifest = _load_manifest()
        self.assertRegex(
            manifest["version"],
            r"^18\.0\.\d+\.\d+\.\d+$",
            "version must follow 18.0.x.y.z",
        )

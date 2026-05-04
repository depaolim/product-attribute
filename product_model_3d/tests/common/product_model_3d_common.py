import ast
import base64
import json
import struct
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from odoo.tests import TransactionCase

MODULE_ROOT = Path(__file__).parent.parent.parent


def _load_manifest():
    return ast.literal_eval((MODULE_ROOT / "__manifest__.py").read_text())


def _make_source(size_kb=1):
    raw = b"x" * (size_kb * 1024)
    return base64.b64encode(raw).decode()


def _make_minimal_stl():
    """Build a minimal valid binary STL (single triangle, 134 bytes)."""
    header = b"\x00" * 80
    num_triangles = struct.pack("<I", 1)
    normal = struct.pack("<fff", 0.0, 0.0, 1.0)
    v1 = struct.pack("<fff", 0.0, 0.0, 0.0)
    v2 = struct.pack("<fff", 1.0, 0.0, 0.0)
    v3 = struct.pack("<fff", 0.0, 1.0, 0.0)
    attr = struct.pack("<H", 0)
    return header + num_triangles + normal + v1 + v2 + v3 + attr


def _make_minimal_glb():
    """Return base64-encoded minimal GLB (valid enough for a copy-through test)."""
    json_content = json.dumps(
        {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": []}]}
    ).encode("utf-8")
    padding = (4 - len(json_content) % 4) % 4
    json_content += b" " * padding
    total_length = 12 + 8 + len(json_content)
    glb = struct.pack("<III", 0x46546C67, 2, total_length)
    glb += struct.pack("<II", len(json_content), 0x4E4F534A)
    glb += json_content
    return base64.b64encode(glb).decode()


VALID_STL_B64 = base64.b64encode(_make_minimal_stl()).decode()
VALID_GLB_B64 = _make_minimal_glb()
VALID_GLTF_B64 = base64.b64encode(b'{"asset":{"version":"2.0"}}').decode()
CORRUPT_SOURCE_B64 = base64.b64encode(b"this is not a 3d file").decode()


class ProductModel3dCommon(TransactionCase):
    """Shared base class for product_model_3d unit tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def patch_pool_cursor(self):
        """Return a context manager that routes pool.cursor() to the test cursor.

        model_3d_run_conversion opens a new cursor to write the failed state so
        it survives a rollback. In tests the record is not committed, so the new
        cursor cannot find it.  Patching keeps everything on the test cursor.
        """
        test_cr = self.env.cr

        @contextmanager
        def _test_cursor():
            yield test_cr

        return patch.object(self.env.registry, "cursor", new=lambda: _test_cursor())

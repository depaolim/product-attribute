import base64
from unittest.mock import patch

from ..common import CORRUPT_SOURCE_B64, VALID_STL_B64, ProductModel3dCommon


class TestConversionWorker(ProductModel3dCommon):
    def _create_stl_template(self):
        return self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": VALID_STL_B64,
                "model_3d_source_filename": "part.stl",
            }
        )

    def _create_corrupt_template(self):
        return self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": CORRUPT_SOURCE_B64,
                "model_3d_source_filename": "bad.stl",
            }
        )

    def test_conversion_happy_path(self):
        template = self._create_stl_template()
        template.model_3d_run_conversion()
        self.assertEqual(template.model_3d_conversion_state, "done")
        self.assertTrue(template.model_3d)
        self.assertTrue(template.model_3d_filename.endswith(".glb"))

    def test_conversion_state_transitions_through_processing(self):
        template = self._create_stl_template()
        captured_states = []
        _original_write = type(template).write

        def _capturing_write(self, vals):
            if "model_3d_conversion_state" in vals:
                captured_states.append(vals["model_3d_conversion_state"])
            return _original_write(self, vals)

        with patch.object(type(template), "write", _capturing_write):
            template.model_3d_run_conversion()

        self.assertGreaterEqual(len(captured_states), 2)
        self.assertEqual(captured_states[0], "processing")
        self.assertIn(captured_states[-1], ("done", "failed"))
        self.assertLess(
            captured_states.index("processing"),
            len(captured_states) - 1,
        )

    def test_conversion_output_is_valid_glb(self):
        template = self._create_stl_template()
        template.model_3d_run_conversion()
        glb_bytes = base64.b64decode(template.model_3d)
        self.assertEqual(glb_bytes[:4], b"glTF")

    def test_conversion_format_derived_from_filename(self):
        import trimesh as _trimesh

        template = self._create_stl_template()
        original_load = _trimesh.load
        captured_kwargs = {}

        def _spy_load(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return original_load(*args, **kwargs)

        with patch.object(_trimesh, "load", side_effect=_spy_load):
            template.model_3d_run_conversion()

        self.assertEqual(captured_kwargs.get("file_type"), "stl")

    def test_conversion_clears_previous_error(self):
        template = self._create_stl_template()
        template.write(
            {
                "model_3d_conversion_state": "processing",
                "model_3d_conversion_error": "previous error",
            }
        )
        template.model_3d_run_conversion()
        self.assertEqual(template.model_3d_conversion_state, "done")
        self.assertFalse(template.model_3d_conversion_error)

    def test_conversion_corrupt_source_sets_failed(self):
        from odoo.addons.queue_job.exception import FailedJobError

        template = self._create_corrupt_template()
        # Use try/except instead of assertRaises context manager: Odoo's
        # _assertRaises wraps the body in a savepoint that is rolled back on
        # exception, which would undo the 'failed' state write we want to verify.
        with self.patch_pool_cursor():
            try:
                template.model_3d_run_conversion()
            except FailedJobError:  # pylint: disable=except-pass
                pass
            else:
                self.fail("FailedJobError was not raised")
        template.invalidate_recordset()
        self.assertEqual(template.model_3d_conversion_state, "failed")
        self.assertTrue(template.model_3d_conversion_error)

    def test_conversion_corrupt_source_raises_failed_job_error(self):
        from odoo.addons.queue_job.exception import FailedJobError

        template = self._create_corrupt_template()
        with self.patch_pool_cursor():
            with self.assertRaises(FailedJobError):
                template.model_3d_run_conversion()

    def test_conversion_failed_state_written_before_raise(self):
        from odoo.addons.queue_job.exception import FailedJobError

        template = self._create_corrupt_template()
        captured_states = []
        _original_write = type(template).write

        def _capturing_write(self, vals):
            if "model_3d_conversion_state" in vals:
                captured_states.append(vals["model_3d_conversion_state"])
            return _original_write(self, vals)

        with self.patch_pool_cursor():
            with patch.object(type(template), "write", _capturing_write):
                with self.assertRaises(FailedJobError):
                    template.model_3d_run_conversion()

        self.assertIn("failed", captured_states)

    def test_conversion_error_message_stored(self):
        from odoo.addons.queue_job.exception import FailedJobError

        template = self._create_corrupt_template()
        with self.patch_pool_cursor():
            try:
                template.model_3d_run_conversion()
            except FailedJobError:  # pylint: disable=except-pass
                pass
            else:
                self.fail("FailedJobError was not raised")
        template.invalidate_recordset()
        self.assertTrue(template.model_3d_conversion_error)
        self.assertGreater(len(template.model_3d_conversion_error), 0)

import base64

from odoo.tests import TransactionCase

from ..common import VALID_GLB_B64, VALID_GLTF_B64, _make_source


class TestJobDispatch(TransactionCase):
    def _create_stl_template(self, **extra):
        vals = {
            "name": "Test Product",
            "model_3d_source": _make_source(1),
            "model_3d_source_filename": "part.stl",
        }
        vals.update(extra)
        return self.env["product.template"].create(vals)

    def test_dispatch_sets_state_queued_for_convertible_format(self):
        template = self._create_stl_template()
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "queued")

    def test_dispatch_writes_job_uuid_for_convertible_format(self):
        template = self._create_stl_template()
        template.action_model_3d_convert()
        self.assertTrue(template.model_3d_job_uuid)

    def test_dispatch_calls_with_delay_correct_args(self):
        template = self._create_stl_template()
        template.action_model_3d_convert()
        job = self.env["queue.job"].search([("uuid", "=", template.model_3d_job_uuid)])
        self.assertEqual(len(job), 1)
        self.assertEqual(job.channel, "root.model_3d_conversion")
        self.assertEqual(job.max_retries, 0)

    def test_glb_source_sets_state_done_synchronously(self):
        template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": VALID_GLB_B64,
                "model_3d_source_filename": "part.glb",
            }
        )
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "done")
        self.assertEqual(
            base64.b64decode(template.model_3d),
            base64.b64decode(template.model_3d_source),
        )
        self.assertEqual(template.model_3d_filename, "part.glb")
        self.assertFalse(template.model_3d_job_uuid)

    def test_gltf_source_sets_state_done_synchronously(self):
        template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": VALID_GLTF_B64,
                "model_3d_source_filename": "part.gltf",
            }
        )
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "done")
        self.assertEqual(template.model_3d_filename, "part.glb")
        self.assertFalse(template.model_3d_job_uuid)

    def test_glb_source_creates_no_queue_job(self):
        template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": VALID_GLB_B64,
                "model_3d_source_filename": "part.glb",
            }
        )
        job_count_before = self.env["queue.job"].search_count([])
        template.action_model_3d_convert()
        self.assertEqual(self.env["queue.job"].search_count([]), job_count_before)

    def test_double_dispatch_aborts_and_requeues_when_queued(self):
        template = self._create_stl_template()
        template.action_model_3d_convert()
        first_uuid = template.model_3d_job_uuid
        self.assertEqual(template.model_3d_conversion_state, "queued")
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "queued")
        self.assertNotEqual(template.model_3d_job_uuid, first_uuid)

    def test_double_dispatch_aborts_and_requeues_when_processing(self):
        template = self._create_stl_template()
        template.write({"model_3d_conversion_state": "processing"})
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "queued")

    def test_failed_record_can_be_requeued(self):
        template = self._create_stl_template()
        template.write(
            {
                "model_3d_conversion_state": "failed",
                "model_3d_conversion_error": "some error",
            }
        )
        template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "queued")
        self.assertFalse(template.model_3d_conversion_error)

    def test_done_record_can_be_replaced(self):
        template = self._create_stl_template()
        template.write({"model_3d_conversion_state": "done"})
        try:
            template.action_model_3d_convert()
        except Exception:
            self.fail("action_model_3d_convert raised unexpectedly for a done record")

    def test_job_uuid_matches_queue_job_record(self):
        template = self._create_stl_template()
        template.action_model_3d_convert()
        job = self.env["queue.job"].search([("uuid", "=", template.model_3d_job_uuid)])
        self.assertEqual(len(job), 1)

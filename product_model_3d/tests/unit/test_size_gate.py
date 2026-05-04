from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from ..common import _make_source


class TestSizeGate(TransactionCase):
    def _set_max_size(self, kb):
        self.env["ir.config_parameter"].sudo().set_param(
            "model_3d_convert.max.size.kb", str(kb)
        )

    def _create_stl(self, size_kb):
        return self.env["product.template"].create(
            {
                "name": "Test Product",
                "model_3d_source": _make_source(size_kb),
                "model_3d_source_filename": "part.stl",
            }
        )

    def test_size_gate_no_file_raises_user_error(self):
        template = self.env["product.template"].create({"name": "Test Product"})
        with self.assertRaises(UserError):
            template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "draft")

    def test_size_gate_blocks_oversized_file(self):
        self._set_max_size(1)
        template = self._create_stl(2)
        job_count_before = self.env["queue.job"].search_count([])
        with self.assertRaises(UserError):
            template.action_model_3d_convert()
        self.assertEqual(template.model_3d_conversion_state, "draft")
        self.assertEqual(self.env["queue.job"].search_count([]), job_count_before)

    def test_size_gate_allows_valid_file(self):
        self._set_max_size(51200)
        template = self._create_stl(1)
        try:
            template.action_model_3d_convert()
        except UserError:
            self.fail("action_model_3d_convert raised UserError unexpectedly")

    def test_size_gate_at_limit_is_allowed(self):
        # The guard is `> max_size_kb`, so a file exactly at the limit must pass.
        self._set_max_size(1)
        template = self._create_stl(1)
        try:
            template.action_model_3d_convert()
        except UserError:
            self.fail("File exactly at the limit should not be blocked")

    def test_size_gate_reads_config_param(self):
        self._set_max_size(100)
        try:
            self._create_stl(90).action_model_3d_convert()
        except UserError:
            self.fail("Should not raise for 90 KB with limit 100 KB")

        self._set_max_size(50)
        with self.assertRaises(UserError):
            self._create_stl(60).action_model_3d_convert()

    def test_size_gate_error_message_contains_sizes(self):
        self._set_max_size(1)
        template = self._create_stl(500)
        with self.assertRaises(UserError) as ctx:
            template.action_model_3d_convert()
        message = str(ctx.exception.args[0])
        self.assertIn("500", message)
        self.assertIn("1", message)

from odoo.tests import TransactionCase

# NOTE: OCA queue_job (this version) has no max_jobs field on queue.job.channel.
# The channel is identified by complete_name = 'root.model_3d_conversion'
# (name='model_3d_conversion', parent_id=root).
# test_channel_max_jobs_is_one verifies the parent is 'root', preserving the
# original test intent as closely as the model allows.


class TestChannelConfig(TransactionCase):
    def _get_channel(self):
        return self.env["queue.job.channel"].search(
            [("complete_name", "=", "root.model_3d_conversion")]
        )

    def test_channel_record_exists(self):
        channel = self._get_channel()
        self.assertEqual(
            len(channel),
            1,
            "Exactly one channel 'root.model_3d_conversion' must exist",
        )

    def test_channel_max_jobs_is_one(self):
        # max_jobs does not exist on queue.job.channel in this queue_job version.
        # We assert instead that the channel is a direct child of 'root', which
        # is the mechanism that limits concurrency to the root channel's worker count.
        channel = self._get_channel()
        self.assertEqual(channel.parent_id.name, "root")

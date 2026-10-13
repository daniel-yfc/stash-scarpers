"""Tests for tasks/stash_client.py (shared GraphQL client)."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "tasks"))

import stash_client
from stash_client import StashConnectionError, graphql


def _fake_run(returncode=0, stdout='{"data": {}}', stderr=""):
    result = mock.Mock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestStashClient(unittest.TestCase):
    def _call(self, env, **run_kwargs):
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch("stash_client.subprocess.run",
                        return_value=_fake_run(**run_kwargs)) as run:
            out = graphql("{ test }")
        return out, run.call_args[0][0]

    def test_no_proxy_when_unset(self):
        _, cmd = self._call({})
        self.assertNotIn("--proxy", cmd)
        self.assertEqual(cmd[-1], "http://localhost:9999/graphql")

    def test_https_proxy_port_rewritten_to_3130(self):
        _, cmd = self._call(
            {"HTTPS_PROXY": "http://user:pass@proxy.example:3128"})
        i = cmd.index("--proxy")
        self.assertEqual(cmd[i + 1], "http://user:pass@proxy.example:3130")

    def test_stash_proxy_used_unchanged(self):
        _, cmd = self._call({
            "STASH_PROXY": "http://proxy.example:9999",
            "HTTPS_PROXY": "http://user:pass@proxy.example:3128",
        })
        i = cmd.index("--proxy")
        self.assertEqual(cmd[i + 1], "http://proxy.example:9999")

    def test_stash_url_env_respected(self):
        _, cmd = self._call({"STASH_URL": "http://stash:9999/graphql"})
        self.assertEqual(cmd[-1], "http://stash:9999/graphql")

    def test_valid_json_returned(self):
        out, _ = self._call({}, stdout='{"data": {"a": 1}}')
        self.assertEqual(out, {"data": {"a": 1}})

    def test_curl_failure_raises(self):
        with self.assertRaises(StashConnectionError):
            self._call({}, returncode=7, stderr="Failed to connect")

    def test_non_json_response_raises(self):
        with self.assertRaises(StashConnectionError):
            self._call({}, stdout="")
        with self.assertRaises(StashConnectionError):
            self._call({}, stdout="not json")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import threading
import time
import unittest
from unittest import mock

from airport_sim.server import app as local_ui
from airport_sim.server import jobs


class BackgroundJobTests(unittest.TestCase):
    def setUp(self) -> None:
        with jobs.JOB_LOCK:
            jobs.JOBS.clear()
            jobs.ACTIVE_JOB_BY_KEY.clear()

    def tearDown(self) -> None:
        with jobs.JOB_LOCK:
            jobs.JOBS.clear()
            jobs.ACTIVE_JOB_BY_KEY.clear()

    def wait_for_terminal(self, job_id: str) -> dict[str, object]:
        for _ in range(200):
            payload = jobs.get_job(job_id)
            if payload and payload["status"] in {"complete", "failed"}:
                return payload
            time.sleep(0.01)
        self.fail(f"background job did not finish: {job_id}")

    def test_same_active_run_is_deduplicated(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def work() -> dict[str, object]:
            started.set()
            if not release.wait(timeout=3):
                raise TimeoutError("test release timed out")
            return {"runId": "seed_7_years_12"}

        logger = mock.Mock()
        first = jobs.submit_job("seed_run", "seed_7_years_12", work, logger=logger)
        self.assertTrue(started.wait(timeout=2))
        second = jobs.submit_job("seed_run", "seed_7_years_12", work, logger=logger)
        self.assertEqual(first["jobId"], second["jobId"])
        self.assertTrue(second["deduplicated"])

        release.set()
        completed = self.wait_for_terminal(str(first["jobId"]))
        self.assertEqual("complete", completed["status"])
        self.assertEqual({"runId": "seed_7_years_12"}, completed["result"])

    def test_failure_is_bounded_and_does_not_expose_multiline_trace(self) -> None:
        def fail() -> dict[str, object]:
            raise RuntimeError("first line\nprivate second line")

        submitted = jobs.submit_job("seed_run", "seed_8_years_12", fail, logger=mock.Mock())
        failed = self.wait_for_terminal(str(submitted["jobId"]))
        self.assertEqual("failed", failed["status"])
        self.assertEqual("first line", failed["error"])

    def test_active_jobs_and_executor_queue_are_bounded(self) -> None:
        release = threading.Event()

        def work() -> dict[str, object]:
            if not release.wait(timeout=3):
                raise TimeoutError("test release timed out")
            return {"ok": True}

        submitted: list[dict[str, object]] = []
        try:
            with mock.patch.object(jobs, "MAX_ACTIVE_JOB_ENTRIES", 2):
                submitted.append(jobs.submit_job("seed_run", "first", work, logger=mock.Mock()))
                submitted.append(jobs.submit_job("seed_run", "second", work, logger=mock.Mock()))
                with self.assertRaises(jobs.JobQueueFullError):
                    jobs.submit_job("seed_run", "third", work, logger=mock.Mock())
                duplicate = jobs.submit_job("seed_run", "first", work, logger=mock.Mock())
                self.assertEqual(submitted[0]["jobId"], duplicate["jobId"])
                self.assertTrue(duplicate["deduplicated"])
                with jobs.JOB_LOCK:
                    self.assertLessEqual(len(jobs.JOBS), 2)
                    self.assertLessEqual(len(jobs.ACTIVE_JOB_BY_KEY), 2)
        finally:
            release.set()
            for job in submitted:
                self.wait_for_terminal(str(job["jobId"]))

    def test_run_job_key_preserves_force_semantics(self) -> None:
        with mock.patch.object(jobs, "submit_job", return_value={"jobId": "test"}) as submit:
            local_ui.submit_run_job(7, 12, False)
            local_ui.submit_run_job(7, 12, True)
        normal_key = submit.call_args_list[0].args[1]
        forced_key = submit.call_args_list[1].args[1]
        self.assertEqual("seed_7_years_12:force=0", normal_key)
        self.assertEqual("seed_7_years_12:force=1", forced_key)
        self.assertNotEqual(normal_key, forced_key)


if __name__ == "__main__":
    unittest.main()

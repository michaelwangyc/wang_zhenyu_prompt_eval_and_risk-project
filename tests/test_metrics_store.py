# -*- coding: utf-8 -*-

import json
from datetime import datetime

from prompt_risk.eval_pipeline import build_report
from prompt_risk.metrics_store import (
    build_latest_key,
    build_run_key,
    upload_metrics,
)


class StubS3Client:
    """Record put_object calls instead of talking to AWS."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str):
        self.objects[f"{Bucket}/{Key}"] = Body


def make_report():
    return build_report(
        case_results=[],
        git_sha="0ea0582abcdef",
        timestamp="2026-07-14T15:30:00Z",
    )


class TestBuildKeys:
    def test_run_key_is_date_partitioned_and_sha_stamped(self):
        key = build_run_key(
            prefix="prompt-risk/metrics",
            timestamp=datetime(2026, 7, 14, 15, 30, 0),
            git_sha="0ea0582abcdef",
        )
        assert key == "prompt-risk/metrics/runs/2026/07/14/20260714T153000Z-0ea0582.json"

    def test_latest_key(self):
        assert build_latest_key("prompt-risk/metrics") == "prompt-risk/metrics/latest.json"


class TestUploadMetrics:
    def test_uploads_run_and_latest(self):
        s3_client = StubS3Client()
        uris = upload_metrics(
            s3_client=s3_client,
            bucket="my-bucket",
            report=make_report(),
        )
        assert uris == [
            "s3://my-bucket/prompt-risk/metrics/runs/2026/07/14/20260714T153000Z-0ea0582.json",
            "s3://my-bucket/prompt-risk/metrics/latest.json",
        ]
        assert len(s3_client.objects) == 2
        for body in s3_client.objects.values():
            doc = json.loads(body)
            assert doc["git_sha"] == "0ea0582abcdef"


if __name__ == "__main__":
    from prompt_risk.tests import run_cov_test

    run_cov_test(
        __file__,
        "prompt_risk.metrics_store",
        preview=False,
    )

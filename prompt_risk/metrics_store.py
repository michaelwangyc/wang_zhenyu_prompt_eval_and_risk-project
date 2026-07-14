# -*- coding: utf-8 -*-

"""S3 persistence for evaluation metrics — the regression-traceability store.

Every evaluation run produces an :class:`~prompt_risk.eval_pipeline.EvalReport`
that this module persists to S3 under two keys:

- a **run key** partitioned by date and stamped with the commit SHA, so the
  full history of evaluation runs can be listed, diffed, and audited::

      {prefix}/runs/2026/07/14/20260714T153000Z-0ea0582.json

- a **latest key** that always points at the most recent run, so dashboards
  and regression checks can fetch the current baseline without a listing::

      {prefix}/latest.json

The approval workflow in CI additionally copies an approved run to
``{prefix}/approved/{git_sha}.json`` after the human deployment gate — see
``.github/workflows/evaluate.yml``.
"""

import typing as T
from datetime import datetime

if T.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

    from .eval_pipeline import EvalReport

DEFAULT_PREFIX = "prompt-risk/metrics"


def build_run_key(
    prefix: str,
    timestamp: datetime,
    git_sha: str,
) -> str:
    """Build the date-partitioned S3 key for one evaluation run."""
    return (
        f"{prefix}/runs/{timestamp:%Y/%m/%d}/"
        f"{timestamp:%Y%m%dT%H%M%SZ}-{git_sha[:7]}.json"
    )


def build_latest_key(prefix: str) -> str:
    """Build the S3 key that always holds the most recent run."""
    return f"{prefix}/latest.json"


def upload_metrics(
    s3_client: "S3Client",
    bucket: str,
    report: "EvalReport",
    prefix: str = DEFAULT_PREFIX,
) -> list[str]:
    """Persist *report* to S3 and return the uploaded S3 URIs.

    Writes the immutable run key first, then overwrites ``latest.json``;
    if the second write fails, the historical record is already safe.
    """
    timestamp = datetime.strptime(report.timestamp, "%Y-%m-%dT%H:%M:%SZ")
    body = report.model_dump_json(indent=2).encode("utf-8")

    uris = []
    for key in [
        build_run_key(prefix=prefix, timestamp=timestamp, git_sha=report.git_sha),
        build_latest_key(prefix=prefix),
    ]:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        uris.append(f"s3://{bucket}/{key}")
    return uris

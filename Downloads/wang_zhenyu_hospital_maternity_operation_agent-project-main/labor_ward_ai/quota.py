# -*- coding: utf-8 -*-

"""
Monthly LLM token / invocation quota tracking.

This module owns:

- ``MonthlyAppQuota`` — PynamoDB ORM model backed by a DynamoDB table whose
  name is read from ``Config.dynamodb_table_name_quota`` (env var
  ``DYNAMODB_TABLE_NAME_QUOTA``).
- ``get_app_id()`` — builds the per-month partition key
  ``yq_hospital_maternity_operation_agent-YYYY-MM`` from the current UTC date.
- ``get_usage()`` — returns the current row, or a zero-initialized in-memory
  instance if the row does not yet exist (no write).
- ``increment_usage()`` — atomic ``UpdateItem(ADD)`` that bumps counters and
  upserts the row if missing. ADD on a missing numeric attribute initializes
  it to 0 first, so first-time callers don't need a separate ``put``.
- ``check_quota()`` — reads counters and raises :class:`QuotaExceededError`
  if the configured caps are hit.

The ``BotoSesManager`` (``bsm``) is **required** by every utility function —
this module has no implicit binding to the ``one`` singleton, so callers
explicitly pass whichever AWS profile / credentials they want the DynamoDB
calls to use. Each call is wrapped in
``pynamodb_session_manager.use_boto_session(MonthlyAppQuota, bsm)``.
"""

import datetime

from boto_session_manager import BotoSesManager
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb_session_manager.api import use_boto_session

from .config.conf_00_def import Config


APP_ID_PREFIX = "wzy_hospital_maternity_operation_agent"

# Read once at import: PynamoDB needs Meta.table_name fixed at class-definition
# time. Loading via Config.new() keeps this module independent of the ``one``
# singleton while still reusing the same env-driven configuration loader.
# Caps (max invokes / max tokens) live on this same Config so all quota knobs
# are tunable from one place.
_config = Config.new()


class MonthlyAppQuota(Model):
    """One row per (app, month). PK is ``app_id``."""

    class Meta:
        table_name = _config.dynamodb_table_name_quota
        region = _config.aws_region

    app_id = UnicodeAttribute(hash_key=True)
    total_input_token = NumberAttribute(default=0)
    total_output_token = NumberAttribute(default=0)
    total_invoke = NumberAttribute(default=0)


class QuotaExceededError(RuntimeError):
    """Raised when the current month's usage has hit a configured cap."""


def get_app_id(now: datetime.datetime | None = None) -> str:
    """Return the per-month partition key for the current (or given) UTC time."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    return f"{APP_ID_PREFIX}-{now.year:04d}-{now.month:02d}"


def get_usage(
    bsm: BotoSesManager,
    app_id: str | None = None,
) -> MonthlyAppQuota:
    """
    Return the quota row for ``app_id``.

    If the row does not exist yet, returns an in-memory ``MonthlyAppQuota``
    with all counters set to 0 (no write is issued).

    :param bsm: AWS session manager used to bind PynamoDB to the right
        credentials for this call. Required — no implicit default.
    """
    if app_id is None:
        app_id = get_app_id()
    with use_boto_session(MonthlyAppQuota, bsm):
        try:
            return MonthlyAppQuota.get(app_id)
        except MonthlyAppQuota.DoesNotExist:
            return MonthlyAppQuota(
                app_id=app_id,
                total_input_token=0,
                total_output_token=0,
                total_invoke=0,
            )


def increment_usage(
    bsm: BotoSesManager,
    input_tokens: int,
    output_tokens: int,
    invokes: int = 1,
    app_id: str | None = None,
) -> None:
    """
    Atomically add to the current month's counters.

    Uses DynamoDB ``UpdateItem`` with ``ADD`` actions, which:

    - upserts the row if it does not exist, and
    - initializes a missing numeric attribute to 0 before adding,

    so callers never need to ``put`` first. This avoids the lost-update race
    that a naive get + set pattern would have under concurrent requests.

    :param bsm: AWS session manager used to bind PynamoDB to the right
        credentials for this call. Required — no implicit default.
    """
    if app_id is None:
        app_id = get_app_id()
    item = MonthlyAppQuota(app_id)
    with use_boto_session(MonthlyAppQuota, bsm):
        item.update(
            actions=[
                MonthlyAppQuota.total_input_token.add(int(input_tokens)),
                MonthlyAppQuota.total_output_token.add(int(output_tokens)),
                MonthlyAppQuota.total_invoke.add(int(invokes)),
            ]
        )


def check_quota(
    bsm: BotoSesManager,
    app_id: str | None = None,
    max_invoke: int | None = None,
    max_input_token: int | None = None,
    max_output_token: int | None = None,
) -> MonthlyAppQuota:
    """
    Read the current month's counters and raise :class:`QuotaExceededError`
    as soon as ANY of the three caps (invoke / input-token / output-token)
    is hit. Returns the row on success.

    :param bsm: AWS session manager used to bind PynamoDB to the right
        credentials for this call. Required — no implicit default.
    :param max_invoke: Override for per-month invoke cap. Defaults to
        ``Config.quota_max_invoke_per_month``.
    :param max_input_token: Override for per-month input-token cap.
        Defaults to ``Config.quota_max_input_token_per_month``.
    :param max_output_token: Override for per-month output-token cap.
        Defaults to ``Config.quota_max_output_token_per_month``.
    """
    if app_id is None:
        app_id = get_app_id()
    if max_invoke is None:
        max_invoke = _config.quota_max_invoke_per_month
    if max_input_token is None:
        max_input_token = _config.quota_max_input_token_per_month
    if max_output_token is None:
        max_output_token = _config.quota_max_output_token_per_month
    usage = get_usage(bsm, app_id)
    if int(usage.total_invoke or 0) >= max_invoke:
        raise QuotaExceededError(
            f"Monthly invoke cap reached for {app_id}: "
            f"{int(usage.total_invoke)} >= {max_invoke}"
        )
    if int(usage.total_input_token or 0) >= max_input_token:
        raise QuotaExceededError(
            f"Monthly input-token cap reached for {app_id}: "
            f"{int(usage.total_input_token)} >= {max_input_token}"
        )
    if int(usage.total_output_token or 0) >= max_output_token:
        raise QuotaExceededError(
            f"Monthly output-token cap reached for {app_id}: "
            f"{int(usage.total_output_token)} >= {max_output_token}"
        )
    return usage

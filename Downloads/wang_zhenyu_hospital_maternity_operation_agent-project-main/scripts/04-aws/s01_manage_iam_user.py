# -*- coding: utf-8 -*-

"""
IAM user lifecycle for the demo app's runtime DynamoDB credentials.

Two top-level functions, both idempotent — re-running is safe:

- ``setup()`` ensures the IAM user, its inline policy (DescribeTable / GetItem
  / Query / UpdateItem on the single quota table), and a fresh access key
  exist. Writes the access key to ``scripts/04-aws/.env``.
- ``teardown()`` deletes the access keys, the inline policy, the user, and
  the local ``.env``. Each step swallows ``NoSuchEntityException`` so partial
  prior runs don't block cleanup.

Comment in / out the call at the bottom and run with::

    .venv/bin/python scripts/04-aws/s01_manage_iam_user.py

The script uses ``one.bsm`` for admin-level IAM API calls. The runtime
credentials it produces are deliberately minimum-privilege — DynamoDB only,
single-table only.
"""

import json
import subprocess
from pathlib import Path

from labor_ward_ai.one.api import one


# Hardcoded — this script manages exactly one user.
IAM_USER_NAME = "wzy_hospital_maternity_operation_agent"
INLINE_POLICY_NAME = "dynamodb_quota_table_access"
INLINE_POLICY_NAME_BEDROCK = "bedrock_invoke_model_access"

ENV_PATH = Path(__file__).resolve().parent / ".env"
GIT_REPO_DIR = Path(__file__).resolve().parents[2]


def _get_repo_url() -> str:
    """Resolve the repo URL from the local git remote ``origin``.

    Normalizes SSH form (``git@host:owner/repo.git``) to HTTPS and strips
    the trailing ``.git`` so the IAM tag value is a clickable browser URL.
    """
    url = subprocess.check_output(
        ["git", "-C", str(GIT_REPO_DIR), "remote", "get-url", "origin"],
        text=True,
    ).strip()
    if url.startswith("git@"):
        host, path = url[len("git@"):].split(":", 1)
        url = f"https://{host}/{path}"
    if url.endswith(".git"):
        url = url[: -len(".git")]
    return url


def _build_user_tags() -> list[dict]:
    # IAM users have no native description field, so we surface the repo URL
    # via tags. Tag keys overwrite on repeat tag_user calls, so this stays
    # idempotent.
    return [
        {"Key": "repo", "Value": _get_repo_url()},
        {"Key": "purpose", "Value": "demo runtime DynamoDB access"},
    ]

DYNAMODB_ACTIONS = [
    "dynamodb:DescribeTable",
    "dynamodb:GetItem",
    "dynamodb:Query",
    "dynamodb:UpdateItem",
]

BEDROCK_ACTIONS = [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
]


def _build_policy_document(table_name: str, region: str, account_id: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": DYNAMODB_ACTIONS,
                "Resource": f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}",
            }
        ],
    }


def _build_bedrock_policy_document(account_id: str) -> dict:
    # Wildcarded on region and model so we don't have to re-run this script
    # every time we swap models or try a new cross-region inference profile.
    # Cross-region profiles (e.g. "us." prefix) require permission on both the
    # profile ARN and the foundation-model ARN in each region they route to.
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": BEDROCK_ACTIONS,
                "Resource": [
                    f"arn:aws:bedrock:*:{account_id}:inference-profile/*",
                    "arn:aws:bedrock:*::foundation-model/*",
                ],
            }
        ],
    }


def setup() -> None:
    """Create / refresh user, policy, and access key. Writes ``.env``."""
    iam = one.bsm.iam_client
    region = one.bsm.aws_region
    account_id = one.bsm.aws_account_id
    table_name = one.config.dynamodb_table_name_quota

    # 1. User — create if missing, otherwise just refresh tags.
    user_tags = _build_user_tags()
    try:
        iam.create_user(UserName=IAM_USER_NAME, Tags=user_tags)
        print(f"[setup] created user: {IAM_USER_NAME}")
    except iam.exceptions.EntityAlreadyExistsException:
        iam.tag_user(UserName=IAM_USER_NAME, Tags=user_tags)
        print(f"[setup] user already exists, refreshed tags: {IAM_USER_NAME}")

    # 2. Inline policies — put_user_policy is upsert. We keep DynamoDB and
    # Bedrock as two separate policies for clear separation of concerns.
    policy_doc = _build_policy_document(table_name, region, account_id)
    iam.put_user_policy(
        UserName=IAM_USER_NAME,
        PolicyName=INLINE_POLICY_NAME,
        PolicyDocument=json.dumps(policy_doc),
    )
    print(
        f"[setup] put inline policy {INLINE_POLICY_NAME!r} "
        f"for table {table_name!r} in {region}"
    )

    bedrock_policy_doc = _build_bedrock_policy_document(account_id)
    iam.put_user_policy(
        UserName=IAM_USER_NAME,
        PolicyName=INLINE_POLICY_NAME_BEDROCK,
        PolicyDocument=json.dumps(bedrock_policy_doc),
    )
    print(f"[setup] put inline policy {INLINE_POLICY_NAME_BEDROCK!r}")

    # 3. Access key — secrets are only returned at creation time, so the only
    # way to keep the local .env in lockstep with AWS is to delete every
    # existing key and mint a fresh one. This rotates on every setup() call,
    # which is the desired idempotent behavior.
    existing = iam.list_access_keys(UserName=IAM_USER_NAME)["AccessKeyMetadata"]
    for key in existing:
        iam.delete_access_key(
            UserName=IAM_USER_NAME, AccessKeyId=key["AccessKeyId"]
        )
        print(f"[setup] deleted old access key: {key['AccessKeyId']}")

    new_key = iam.create_access_key(UserName=IAM_USER_NAME)["AccessKey"]
    print(f"[setup] created new access key: {new_key['AccessKeyId']}")

    # 4. Write to local .env. Top-level .gitignore covers .env at any depth.
    ENV_PATH.write_text(
        f"AWS_ACCESS_KEY_ID={new_key['AccessKeyId']}\n"
        f"AWS_SECRET_ACCESS_KEY={new_key['SecretAccessKey']}\n"
        f"AWS_REGION={region}\n",
        encoding="utf-8",
    )
    print(f"[setup] wrote credentials to: {ENV_PATH}")


def teardown() -> None:
    """Delete access keys, inline policy, user, and local ``.env``."""
    iam = one.bsm.iam_client

    # 1. Access keys (must be removed before the user can be deleted).
    try:
        keys = iam.list_access_keys(UserName=IAM_USER_NAME)["AccessKeyMetadata"]
        for key in keys:
            iam.delete_access_key(
                UserName=IAM_USER_NAME, AccessKeyId=key["AccessKeyId"]
            )
            print(f"[teardown] deleted access key: {key['AccessKeyId']}")
    except iam.exceptions.NoSuchEntityException:
        print("[teardown] user absent, skipping access-key cleanup")

    # 2. Inline policies.
    for policy_name in (INLINE_POLICY_NAME, INLINE_POLICY_NAME_BEDROCK):
        try:
            iam.delete_user_policy(UserName=IAM_USER_NAME, PolicyName=policy_name)
            print(f"[teardown] deleted inline policy: {policy_name}")
        except iam.exceptions.NoSuchEntityException:
            print(f"[teardown] inline policy {policy_name!r} already absent")

    # 3. User.
    try:
        iam.delete_user(UserName=IAM_USER_NAME)
        print(f"[teardown] deleted user: {IAM_USER_NAME}")
    except iam.exceptions.NoSuchEntityException:
        print(f"[teardown] user {IAM_USER_NAME!r} already absent")

    # 4. Local .env.
    if ENV_PATH.exists():
        ENV_PATH.unlink()
        print(f"[teardown] removed: {ENV_PATH}")
    else:
        print(f"[teardown] {ENV_PATH} already absent")


if __name__ == "__main__":
    setup()
    # teardown()

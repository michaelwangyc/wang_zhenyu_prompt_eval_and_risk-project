# -*- coding: utf-8 -*-

import typing as T
import os
from functools import cached_property

import boto3

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_01_main import One


class OneBotoSesMixin:
    @cached_property
    def boto_ses(self: "One") -> boto3.Session:
        # Local development uses a named AWS profile.  In CI (GitHub Actions
        # OIDC) credentials come from the default provider chain instead —
        # set PROMPT_RISK_AWS_PROFILE="" to bypass the profile lookup.
        profile_name = os.environ.get("PROMPT_RISK_AWS_PROFILE", "wang_zhenyu_dev")
        return boto3.Session(
            profile_name=profile_name or None,
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )

    @cached_property
    def bedrock_runtime_client(self: "One"):
        return self.boto_ses.client("bedrock-runtime")

    @cached_property
    def s3_client(self: "One"):
        return self.boto_ses.client("s3")

# -*- coding: utf-8 -*-

"""AWS Boto3 mixin for the One class."""

import typing as T
from functools import cached_property

import boto3
from boto_session_manager import BotoSesManager

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One
    from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient


class Boto3Mixin:
    """Mixin providing AWS session and Bedrock client access."""
    @cached_property
    def bsm(self: "One") -> BotoSesManager:
        """BotoSesManager wrapping the same credentials as ``boto_ses``.

        Used by ``pynamodb_session_manager.use_boto_session`` to bind PynamoDB
        models to the configured AWS profile/credentials at call time.
        """
        return BotoSesManager(
            region_name=self.config.aws_region,
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key,
        )

    @cached_property
    def boto_ses(self: "One") -> boto3.Session:
        """Create a boto3 session with configured AWS credentials."""
        return self.bsm.boto_ses

    def bedrock_runtime_client(self: "One") -> "BedrockRuntimeClient":
        """Get the Bedrock Runtime client for invoking models."""
        return self.boto_ses.client("bedrock-runtime")

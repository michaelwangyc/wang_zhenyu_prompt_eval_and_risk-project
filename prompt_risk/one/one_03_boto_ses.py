# -*- coding: utf-8 -*-

import typing as T
from functools import cached_property

import boto3

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_01_main import One


class OneBotoSesMixin:
    @cached_property
    def boto_ses(self: "One") -> boto3.Session:
        return boto3.Session(
            profile_name="wang_zhenyu_dev",
            region_name="us-east-1",
        )

    @cached_property
    def bedrock_runtime_client(self: "One"):
        return self.boto_ses.client("bedrock-runtime")

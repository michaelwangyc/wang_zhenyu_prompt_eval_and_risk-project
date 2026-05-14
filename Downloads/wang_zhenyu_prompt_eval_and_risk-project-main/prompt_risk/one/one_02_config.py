# -*- coding: utf-8 -*-

import typing as T
from functools import cached_property

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_01_main import One


class OneConfigMixin:
    @cached_property
    def config(self: "One"):
        return None

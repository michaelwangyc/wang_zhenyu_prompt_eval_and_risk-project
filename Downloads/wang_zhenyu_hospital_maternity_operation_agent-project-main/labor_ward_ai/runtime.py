# -*- coding: utf-8 -*-

"""
Runtime detection module.

The Runtime class may seem redundant at first glance, but it's designed for
ergonomic usage across the codebase. Import once and use everywhere:

    from .runtime import runtime

    if runtime.is_local():
        ...

One place complex, everywhere else simple. Your IDE will autocomplete everything.
"""

import os
import enum

from functools import cached_property


class RuntimeEnum(str, enum.Enum):
    LOCAL = "LOCAL"
    VERCEL = "VERCEL"


class Runtime:
    """Singleton-style runtime detector. Use the `runtime` instance, not this class."""

    @cached_property
    def name(self) -> str:
        if os.environ.get("VERCEL", "NOTHING") == "1":
            return RuntimeEnum.VERCEL.value
        else:
            return RuntimeEnum.LOCAL.value

    def is_local(self) -> bool:
        return self.name == RuntimeEnum.LOCAL.value

    def is_vercel(self) -> bool:
        return self.name == RuntimeEnum.VERCEL.value


runtime = Runtime()

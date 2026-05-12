# -*- coding: utf-8 -*-

"""Configuration mixin module for the One class."""

import typing as T
from functools import cached_property
from ..config.conf_00_def import Config

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class ConfigMixin:
    """Mixin class that provides configuration access to the One class."""

    @cached_property
    def config(self: "One") -> "Config":
        """Return the cached configuration instance."""
        return Config.new()

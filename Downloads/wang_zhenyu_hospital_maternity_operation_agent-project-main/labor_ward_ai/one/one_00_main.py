# -*- coding: utf-8 -*-

"""Main module defining the One class that aggregates all mixins."""

from .one_01_config import ConfigMixin
from .one_02_db import DbMixin
from .one_03_boto3 import Boto3Mixin
from .one_04_agent import AgentMixin

class One(
    ConfigMixin,
    DbMixin,
    Boto3Mixin,
    AgentMixin,
):
    """Central class that combines all mixin functionalities for the application."""


one = One()

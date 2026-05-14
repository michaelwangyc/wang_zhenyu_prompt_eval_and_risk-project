# -*- coding: utf-8 -*-

import enum
import tomllib
from functools import cached_property

from pydantic import BaseModel

from ...constants import PromptIdEnum

from .p2_classification_runner import P2ClassificationUserPromptData


class P2ClassificationUserPromptDataLoader(BaseModel):
    type: str
    name: str

    @cached_property
    def _toml(self) -> dict:
        path = PromptIdEnum.UC1_P2_CLASSIFICATION.dir_root.joinpath(
            self.type,
            f"{self.name}.toml",
        )
        return tomllib.loads(path.read_text())

    @cached_property
    def data(self) -> "P2ClassificationUserPromptData":
        return P2ClassificationUserPromptData(**self._toml["input"])

    @cached_property
    def expected(self) -> dict | None:
        return self._toml.get("expected")

    @cached_property
    def attack_target(self) -> dict | None:
        return self._toml.get("attack_target")


P2Loader = P2ClassificationUserPromptDataLoader


class P2ClassificationUserPromptDataLoaderEnum(enum.Enum):
    # fmt: off
    a_01_injection_in_extracted_fields = P2Loader(type="attack", name="a-01-injection-in-extracted-fields")
    a_02_lob_hint_poisoned             = P2Loader(type="attack", name="a-02-lob-hint-poisoned")
    a_03_severity_downgrade_via_fields  = P2Loader(type="attack", name="a-03-severity-downgrade-via-fields")
    b_01_auto_rear_end                  = P2Loader(type="normal", name="b-01-auto-rear-end")
    b_02_property_fire                  = P2Loader(type="normal", name="b-02-property-fire")
    b_03_workers_comp_fall              = P2Loader(type="normal", name="b-03-workers-comp-fall")
    b_04_gl_slip_and_fall               = P2Loader(type="normal", name="b-04-gl-slip-and-fall")
    b_05_auto_multi_vehicle             = P2Loader(type="normal", name="b-05-auto-multi-vehicle")
    b_06_ambiguous_auto_property        = P2Loader(type="normal", name="b-06-ambiguous-auto-property")
    # fmt: on


P2LoaderEnum = P2ClassificationUserPromptDataLoaderEnum

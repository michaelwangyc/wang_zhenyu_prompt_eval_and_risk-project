# -*- coding: utf-8 -*-

import enum
import tomllib
from functools import cached_property

from pydantic import BaseModel

from ...constants import PromptIdEnum

from .p1_extraction_runner import P1ExtractionUserPromptData


class P1ExtractionUserPromptDataLoader(BaseModel):
    type: str
    name: str

    @cached_property
    def _toml(self) -> dict:
        path = PromptIdEnum.UC1_P1_EXTRACTION.dir_root.joinpath(
            self.type,
            f"{self.name}.toml",
        )
        return tomllib.loads(path.read_text())

    @cached_property
    def data(self) -> "P1ExtractionUserPromptData":
        return P1ExtractionUserPromptData(**self._toml["input"])

    @cached_property
    def expected(self) -> dict | None:
        return self._toml.get("expected")

    @cached_property
    def attack_target(self) -> dict | None:
        return self._toml.get("attack_target")


P1Loader = P1ExtractionUserPromptDataLoader


class P1ExtractionUserPromptDataLoaderEnum(enum.Enum):
    # fmt: off
    a_01_injection_in_narrative = P1Loader(type="attack", name="a-01-injection-in-narrative")
    a_02_hidden_instructions    = P1Loader(type="attack", name="a-02-hidden-instructions")
    a_03_role_confusion         = P1Loader(type="attack", name="a-03-role-confusion")
    b_01_auto_rear_end          = P1Loader(type="normal", name="b-01-auto-rear-end")
    b_02_property_fire          = P1Loader(type="normal", name="b-02-property-fire")
    b_03_workers_comp_fall      = P1Loader(type="normal", name="b-03-workers-comp-fall")
    b_04_gl_slip_and_fall       = P1Loader(type="normal", name="b-04-gl-slip-and-fall")
    b_05_auto_multi_vehicle     = P1Loader(type="normal", name="b-05-auto-multi-vehicle")
    b_06_ambiguous_lob          = P1Loader(type="normal", name="b-06-ambiguous-lob")
    # fmt: on


P1LoaderEnum = P1ExtractionUserPromptDataLoaderEnum

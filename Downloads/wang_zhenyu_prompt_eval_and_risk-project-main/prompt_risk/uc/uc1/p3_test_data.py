# -*- coding: utf-8 -*-

import enum
import tomllib
from functools import cached_property

from pydantic import BaseModel

from ...constants import PromptIdEnum

from .p3_triage_runner import P3TriageUserPromptData


class P3TriageUserPromptDataLoader(BaseModel):
    type: str
    name: str

    @cached_property
    def _toml(self) -> dict:
        path = PromptIdEnum.UC1_P3_TRIAGE.dir_root.joinpath(
            self.type,
            f"{self.name}.toml",
        )
        return tomllib.loads(path.read_text())

    @cached_property
    def data(self) -> "P3TriageUserPromptData":
        return P3TriageUserPromptData(**self._toml["input"])

    @cached_property
    def expected(self) -> dict | None:
        return self._toml.get("expected")

    @cached_property
    def attack_target(self) -> dict | None:
        return self._toml.get("attack_target")


P3Loader = P3TriageUserPromptDataLoader


class P3TriageUserPromptDataLoaderEnum(enum.Enum):
    # fmt: off
    a_01_severity_downgrade_in_extraction   = P3Loader(type="attack", name="a-01-severity-downgrade-in-extraction")
    a_02_classification_mismatch            = P3Loader(type="attack", name="a-02-classification-mismatch")
    a_03_override_instructions_in_description = P3Loader(type="attack", name="a-03-override-instructions-in-description")
    b_01_auto_minor_no_injury               = P3Loader(type="normal", name="b-01-auto-minor-no-injury")
    b_02_property_fire_high                 = P3Loader(type="normal", name="b-02-property-fire-high")
    b_03_workers_comp_moderate_injury       = P3Loader(type="normal", name="b-03-workers-comp-moderate-injury")
    b_04_gl_slip_and_fall                   = P3Loader(type="normal", name="b-04-gl-slip-and-fall")
    b_05_auto_multi_vehicle_severe          = P3Loader(type="normal", name="b-05-auto-multi-vehicle-severe")
    b_06_ambiguous_escalated_from_p2        = P3Loader(type="normal", name="b-06-ambiguous-escalated-from-p2")
    # fmt: on


P3LoaderEnum = P3TriageUserPromptDataLoaderEnum

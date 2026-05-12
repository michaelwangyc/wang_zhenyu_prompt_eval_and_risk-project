# -*- coding: utf-8 -*-

import enum
from pathlib import Path

from .paths import path_enum


class UseCaseIdEnum(enum.StrEnum):
    """Registry of use-case identifiers."""
    JUDGE = "judges"
    UC1_CLAIM_INTAKE = "uc1-claim-intake"


class PromptIdEnum(enum.StrEnum):
    """Registry of prompt identifiers, formatted as ``{use_case_id}:{short_name}``."""
    JUDGE_J1_OVER_PERMISSIVE = f"{UseCaseIdEnum.JUDGE.value}:j1-over-permissive"
    UC1_P1_EXTRACTION = f"{UseCaseIdEnum.UC1_CLAIM_INTAKE.value}:p1-extraction"
    UC1_P1_EXTRACTION_JUDGE = f"{UseCaseIdEnum.UC1_CLAIM_INTAKE.value}:p1-extraction-judge"
    UC1_P2_CLASSIFICATION = f"{UseCaseIdEnum.UC1_CLAIM_INTAKE.value}:p2-classification"
    UC1_P3_TRIAGE = f"{UseCaseIdEnum.UC1_CLAIM_INTAKE.value}:p3-triage"

    @property
    def use_case_id(self) -> str:
        return self.value.split(":", 1)[0]

    @property
    def short_name(self) -> str:
        return self.value.split(":", 1)[1]

    @property
    def dir_root(self) -> Path:
        return path_enum.dir_data.joinpath(
            self.use_case_id,
            "prompts",
            self.short_name,
        )

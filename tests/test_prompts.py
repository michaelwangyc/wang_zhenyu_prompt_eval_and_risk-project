# -*- coding: utf-8 -*-

from prompt_risk.prompts import Prompt
from prompt_risk.constants import PromptIdEnum


def test_read_prompt():
    prompt = Prompt(
        id=PromptIdEnum.JUDGE_J1_OVER_PERMISSIVE.value,
        version="01",
    )
    _ = prompt.system_prompt_template.render()

    prompt = Prompt(
        id=PromptIdEnum.UC1_P1_EXTRACTION.value,
        version="01",
    )
    _ = prompt.system_prompt_template.render()


if __name__ == "__main__":
    from prompt_risk.tests import run_cov_test

    run_cov_test(
        __file__,
        "prompt_risk.prompts",
        preview=False,
    )

# -*- coding: utf-8 -*-

"""
Run J1 Over-Permissive Authorization Judge on UC1-P1 prompt.

Pin a judge version and a prompt version, then iterate through all test data
loaders (normal + attack) to evaluate the prompt with each concrete input.
"""

from prompt_risk.uc.uc1.j1_uc1_p1 import run_j1_on_uc1_p1
from prompt_risk.uc.uc1.p1_test_data import P1LoaderEnum
from prompt_risk.judges.j1_over_permissive import print_j1_result
from prompt_risk.one.api import one

client = one.bedrock_runtime_client

JUDGE_VERSION = "01"

PROMPT_VERSION = "01"
# PROMPT_VERSION = "02"
# PROMPT_VERSION = "03"
# PROMPT_VERSION = "04"

loader_entry = P1LoaderEnum.a_01_injection_in_narrative
# loader_entry = P1LoaderEnum.a_02_hidden_instructions
# loader_entry = P1LoaderEnum.a_03_role_confusion

loader = loader_entry.value
print(f"\n{'='*60}")
print(f"[{loader_entry.name}] {loader.type}/{loader.name}")
print(f"{'='*60}")

result = run_j1_on_uc1_p1(
    client=client,
    # loader=loader,
    prompt_version=PROMPT_VERSION,
    judge_version=JUDGE_VERSION,
)
print_j1_result(result)

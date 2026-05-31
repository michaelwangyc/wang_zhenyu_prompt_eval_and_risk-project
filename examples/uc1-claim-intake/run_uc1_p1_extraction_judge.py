# -*- coding: utf-8 -*-

"""
Run P1 Extraction Judge on UC1-P1 output.

First runs the extraction prompt to get LLM output, then feeds the
original input + extraction output to the judge for evaluation.
"""

from prompt_risk.uc.uc1.p1_extraction_runner import run_p1_extraction
from prompt_risk.uc.uc1.p1_extraction_judge_runner import (
    run_p1_extraction_judge,
    P1ExtractionJudgeUserPromptData,
)
from prompt_risk.uc.uc1.p1_test_data import P1LoaderEnum
from prompt_risk.one.api import one

client = one.bedrock_runtime_client

EXTRACTION_VERSION = "01"
JUDGE_VERSION = "01"

# case = P1LoaderEnum.a_01_injection_in_narrative
# case = P1LoaderEnum.a_02_hidden_instructions
# case = P1LoaderEnum.a_03_role_confusion
# case = P1LoaderEnum.b_01_auto_rear_end
# case = P1LoaderEnum.b_02_property_fire
# case = P1LoaderEnum.b_03_workers_comp_fall
# case = P1LoaderEnum.b_04_gl_slip_and_fall
# case = P1LoaderEnum.b_05_auto_multi_vehicle
case = P1LoaderEnum.b_06_ambiguous_lob

loader = case.value
print(f"\n{'='*60}")
print(f"[{case.name}]  {loader.type}/{loader.name}")
print(f"{'='*60}")

# Step 1: run extraction
print("\n--- Extraction ---")
extraction_output = run_p1_extraction(
    client=client,
    data=loader.data,
    prompt_version=EXTRACTION_VERSION,
)
print(extraction_output.model_dump_json(indent=2))

# Step 2: run judge on the extraction result
print("\n--- Judge ---")
judge_data = P1ExtractionJudgeUserPromptData(
    input=loader.data.model_dump_json(indent=2),
    output=extraction_output.model_dump_json(indent=2),
)
judge_output = run_p1_extraction_judge(
    client=client,
    data=judge_data,
    prompt_version=JUDGE_VERSION,
)
icon = "🟢" if judge_output.pass_ else "🔴"
print(f"{icon} pass: {judge_output.pass_}")
print(f"reason: {judge_output.reason}")
if judge_output.field_errors:
    print("field_errors:")
    for fe in judge_output.field_errors:
        print(f"  - {fe.field}: {fe.issue}")

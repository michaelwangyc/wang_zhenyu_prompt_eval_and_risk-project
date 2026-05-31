# -*- coding: utf-8 -*-

from prompt_risk.uc.uc1.p1_extraction_runner import run_p1_extraction
from prompt_risk.uc.uc1.p1_test_data import P1LoaderEnum
from prompt_risk.evaluations import evaluate, print_eval_result
from prompt_risk.one.api import one

client = one.bedrock_runtime_client

case = P1LoaderEnum.a_01_injection_in_narrative
# case = P1LoaderEnum.a_02_hidden_instructions
# case = P1LoaderEnum.a_03_role_confusion
# case = P1LoaderEnum.b_01_auto_rear_end
# case = P1LoaderEnum.b_02_property_fire
# case = P1LoaderEnum.b_03_workers_comp_fall
# case = P1LoaderEnum.b_04_gl_slip_and_fall
# case = P1LoaderEnum.b_05_auto_multi_vehicle
# case = P1LoaderEnum.b_06_ambiguous_lob

loader = case.value
print(f"\n{'='*60}")
print(f"{case.name}  ({loader.type}/{loader.name})")

output = run_p1_extraction(client=client, data=loader.data, prompt_version="01")

if loader.expected or loader.attack_target:
    result = evaluate(output, loader.expected, loader.attack_target)
    print_eval_result(result, output)
else:
    print("  (no assertions defined)")
    print(output)

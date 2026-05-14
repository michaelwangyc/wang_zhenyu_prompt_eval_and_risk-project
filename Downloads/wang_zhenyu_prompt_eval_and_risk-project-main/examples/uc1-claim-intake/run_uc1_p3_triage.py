# -*- coding: utf-8 -*-

from prompt_risk.uc.uc1.p3_triage_runner import run_p3_triage
from prompt_risk.uc.uc1.p3_test_data import P3LoaderEnum
from prompt_risk.evaluations import evaluate, print_eval_result
from prompt_risk.one.api import one

client = one.bedrock_runtime_client

case = P3LoaderEnum.a_01_severity_downgrade_in_extraction
# case = P3LoaderEnum.a_02_classification_mismatch
# case = P3LoaderEnum.a_03_override_instructions_in_description
# case = P3LoaderEnum.b_01_auto_minor_no_injury
# case = P3LoaderEnum.b_02_property_fire_high
# case = P3LoaderEnum.b_03_workers_comp_moderate_injury
# case = P3LoaderEnum.b_04_gl_slip_and_fall
# case = P3LoaderEnum.b_05_auto_multi_vehicle_severe
# case = P3LoaderEnum.b_06_ambiguous_escalated_from_p2

loader = case.value
print(f"\n{'='*60}")
print(f"{case.name}  ({loader.type}/{loader.name})")

output = run_p3_triage(client=client, data=loader.data, prompt_version="01")

if loader.expected or loader.attack_target:
    result = evaluate(output, loader.expected, loader.attack_target)
    print_eval_result(result, output)
else:
    print("  (no assertions defined)")
    print(output)

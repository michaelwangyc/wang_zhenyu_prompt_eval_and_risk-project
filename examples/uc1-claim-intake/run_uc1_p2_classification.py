# -*- coding: utf-8 -*-

from prompt_risk.uc.uc1.p2_classification_runner import run_p2_classification
from prompt_risk.uc.uc1.p2_test_data import P2LoaderEnum
from prompt_risk.evaluations import evaluate, print_eval_result
from prompt_risk.one.api import one

client = one.bedrock_runtime_client

case = P2LoaderEnum.a_01_injection_in_extracted_fields
# case = P2LoaderEnum.a_02_lob_hint_poisoned
# case = P2LoaderEnum.a_03_severity_downgrade_via_fields
# case = P2LoaderEnum.b_01_auto_rear_end
# case = P2LoaderEnum.b_02_property_fire
# case = P2LoaderEnum.b_03_workers_comp_fall
# case = P2LoaderEnum.b_04_gl_slip_and_fall
# case = P2LoaderEnum.b_05_auto_multi_vehicle
# case = P2LoaderEnum.b_06_ambiguous_auto_property

loader = case.value
print(f"\n{'='*60}")
print(f"{case.name}  ({loader.type}/{loader.name})")

output = run_p2_classification(client=client, data=loader.data, prompt_version="01")

if loader.expected or loader.attack_target:
    result = evaluate(output, loader.expected, loader.attack_target)
    print_eval_result(result, output)
else:
    print("  (no assertions defined)")
    print(output)

# -*- coding: utf-8 -*-

from prompt_risk.uc.uc1.p1_extraction_runner import run_p1_extraction
from prompt_risk.uc.uc1.p1_test_data import P1LoaderEnum
from prompt_risk.evaluations import evaluate, print_eval_result
from prompt_risk.one.api import one


def test():
    client = one.bedrock_runtime_client
    current_golden_version = "01"

    for case in P1LoaderEnum:
        loader = case.value
        print(f"\n{'='*60}")
        print(f"{case.name}  ({loader.type}/{loader.name})")

        output = run_p1_extraction(
            client=client,
            data=loader.data,
            prompt_version=current_golden_version,
        )

        if loader.expected or loader.attack_target:
            result = evaluate(output, loader.expected, loader.attack_target)
            print_eval_result(result)
        else:
            print("  (no assertions defined)")
            print(output)


if __name__ == "__main__":
    from prompt_risk.tests import run_unit_test

    run_unit_test(__file__)

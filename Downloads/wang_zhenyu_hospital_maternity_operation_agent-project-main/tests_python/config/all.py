# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from labor_ward_ai.tests import run_cov_test

    run_cov_test(
        __file__,
        "labor_ward_ai.config",
        is_folder=True,
        preview=False,
    )
# -*- coding: utf-8 -*-

from labor_ward_ai.one.one_00_main import one


def test_one():
    _ = one


if __name__ == "__main__":
    from labor_ward_ai.tests import run_cov_test

    run_cov_test(
        __file__,
        "labor_ward_ai.one.one_00_main",
        preview=False,
    )

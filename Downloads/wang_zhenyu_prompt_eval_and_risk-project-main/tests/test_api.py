# -*- coding: utf-8 -*-

from prompt_risk import api


def test():
    _ = api


if __name__ == "__main__":
    from prompt_risk.tests import run_cov_test

    run_cov_test(
        __file__,
        "prompt_risk.api",
        preview=False,
    )

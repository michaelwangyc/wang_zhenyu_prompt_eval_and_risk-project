# -*- coding: utf-8 -*-

from labor_ward_ai.one.one_00_main import one


class TestDbMixin:
    def test_database_schema_str(self):
        _ = one.database_schema_str

    def test_execute_and_print_result(self):
        sql = "SELECT 1;"
        _ = one.execute_and_print_result(sql)


if __name__ == "__main__":
    from labor_ward_ai.tests import run_cov_test

    run_cov_test(
        __file__,
        "labor_ward_ai.one.one_02_db",
        preview=False,
    )

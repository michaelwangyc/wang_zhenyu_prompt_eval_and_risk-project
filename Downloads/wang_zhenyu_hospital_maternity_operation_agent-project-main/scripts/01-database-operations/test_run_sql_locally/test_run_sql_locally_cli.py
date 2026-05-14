# -*- coding: utf-8 -*-

import fire
from labor_ward_ai.sql_utils import execute_and_print_result
from labor_ward_ai.one.api import one


def main(sql: str):
    execute_and_print_result(engine=one.local_sqlite_engine, sql=sql)


if __name__ == "__main__":
    fire.Fire(main)

# -*- coding: utf-8 -*-

import typing as T

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from tabulate import tabulate


DEFAULT_MAX_ROWS = 200
DEFAULT_MAX_CHARS = 20000


def format_result(
    result: T.Union["sa.CursorResult", "sa.Result"],
    max_rows: int = DEFAULT_MAX_ROWS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Format SQL query result into a Markdown table.

    .. note::

        Markdown tables are the optimal format for presenting SQL query results to LLMs,
        offering the best combination of token efficiency, comprehension, and maintainability.

        - Token Efficiency: Uses 24% fewer tokens than JSON, reducing API costs
            and fitting more data within context limits
        - Natural LLM Comprehension: Aligns with LLM training data patterns,
            enabling better understanding compared to nested JSON/XML structures
        - Balanced Readability: Maintains both machine parsability and human readability
            for seamless debugging and maintenance

    :param max_rows: Maximum number of rows to keep. Anything beyond this is dropped
        with a truncation note appended, so unbounded ``SELECT *`` queries cannot
        blow up the LLM context.
    :param max_chars: Hard cap on the final string length, applied after row
        truncation as a last-resort defense against very wide rows.
    """
    records = result.fetchmany(max_rows + 1)
    if len(records) == 0:
        return "No result"

    truncated_rows = len(records) > max_rows
    if truncated_rows:
        records = records[:max_rows]

    rows = list()
    columns = result.keys()
    rows.append(columns)
    for record in records:
        rows.append(list(record))

    text = tabulate(
        rows,
        headers="firstrow",
        tablefmt="pipe",
        floatfmt=".4f",
    )

    if truncated_rows:
        text += (
            f"\n\n_Note: result truncated to first {max_rows} rows; "
            f"more rows exist. Add a tighter WHERE/LIMIT clause to see them._"
        )

    if len(text) > max_chars:
        text = (
            text[:max_chars]
            + f"\n\n_Note: output truncated to {max_chars} characters._"
        )

    return text


def ensure_valid_select_query(query: str):
    """
    Ensure the query is a valid SELECT statement.
    """
    if query.upper().strip().startswith("SELECT ") is False:
        raise ValueError("Invalid query: must start with 'SELECT '")


def execute_and_print_result(
    engine: "sa.Engine",
    sql: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Execute a SQL query and print the result as a Markdown table.

    This is a convenience function for interactive exploration and debugging.
    It combines query execution with formatted console output.

    :param engine: SQLAlchemy engine instance connected to the database.
    :param sql: Raw SQL query string to execute.
    :param max_rows: Forwarded to :func:`format_result`.
    :param max_chars: Forwarded to :func:`format_result`.

    :return: The query result formatted as a Markdown table string.
    """
    try:
        ensure_valid_select_query(sql)
    except ValueError as e:  # pragma: no cover
        return f"Error: {e}"

    stmt = sa.text(sql)
    with engine.connect() as conn:
        try:
            result = conn.execute(stmt)
        except sa_exc.OperationalError as e:  # pragma: no cover
            return f"Error executing query: {e._message()}"
        except Exception as e:  # pragma: no cover
            return f"Error executing query: {e}"

        try:
            text = format_result(result, max_rows=max_rows, max_chars=max_chars)
        except Exception as e:  # pragma: no cover
            return f"Error formatting result: {e}"

        print(text)
        return text

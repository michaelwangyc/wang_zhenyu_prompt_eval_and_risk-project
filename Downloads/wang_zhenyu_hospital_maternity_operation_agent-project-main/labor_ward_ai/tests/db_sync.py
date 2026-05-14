# -*- coding: utf-8 -*-

"""
Database sync utilities for testing.

This module provides functions to sync data between local SQLite and remote PostgreSQL,
useful for resetting database state during testing.
"""

import sqlalchemy as sa

# Table insertion order based on foreign key dependencies.
# Tables are inserted in this order to avoid FK constraint violations.
# Drop order is the reverse.
TABLE_INSERT_ORDER = [
    # Independent tables (no FK dependencies)
    "patient",
    "provider",
    "room",
    # Depends on patient
    "ob_profile",
    # Depends on provider
    "shift",
    # Depends on patient, ob_profile, provider
    # NOTE: current_bed_id is circular dependency, will be updated later
    "admission",
    # Depends on room, admission
    "bed",
    # Depends on admission
    "labor_progress",
    "vital_sign",
    # Depends on admission, provider, room
    "medical_order",
    # Depends on admission, provider
    "alert",
]


def sync_sqlite_to_postgres(
    local_engine: sa.Engine,
    remote_engine: sa.Engine,
    verbose: bool = True,
) -> dict:
    """
    Sync local SQLite database to remote PostgreSQL database.

    This function is idempotent - it will drop all tables and recreate them.

    Args:
        local_engine: SQLAlchemy engine connected to local SQLite database.
        remote_engine: SQLAlchemy engine connected to remote PostgreSQL database.
        verbose: If True, print progress messages.

    Returns:
        dict: Summary of the sync operation with row counts per table.
    """

    def log(msg: str):
        if verbose:
            print(msg)

    log("Sync sqlite to remote database...")

    # Step 1: Reflect local database schema
    log("Reflecting local SQLite schema...")
    local_metadata = sa.MetaData()
    local_metadata.reflect(bind=local_engine)

    # Verify all expected tables exist
    local_table_names = set(local_metadata.tables.keys())
    expected_tables = set(TABLE_INSERT_ORDER)
    missing_tables = expected_tables - local_table_names
    if missing_tables:
        raise ValueError(f"Missing tables in local database: {missing_tables}")

    extra_tables = local_table_names - expected_tables
    if extra_tables:
        log(
            f"Warning: Extra tables in local database (will be ignored): {extra_tables}"
        )

    # Step 2: Read all data from local database
    log("Reading data from local SQLite...")
    local_data = {}
    with local_engine.connect() as conn:
        for table_name in TABLE_INSERT_ORDER:
            result = conn.execute(sa.text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            columns = result.keys()
            local_data[table_name] = {
                "columns": list(columns),
                "rows": [dict(zip(columns, row)) for row in rows],
            }
            log(f"  {table_name}: {len(rows)} rows")

    # Step 3: Drop all tables in remote database (reverse order)
    log("Dropping tables in remote PostgreSQL...")
    with remote_engine.begin() as conn:
        # Disable FK checks temporarily for clean drop
        for table_name in reversed(TABLE_INSERT_ORDER):
            conn.execute(sa.text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            log(f"  Dropped: {table_name}")

    # Step 4: Create tables in remote database
    log("Creating tables in remote PostgreSQL...")

    # Create a new metadata for remote, copying structure from local
    # We need to handle SQLite -> PostgreSQL type conversions
    remote_metadata = sa.MetaData()

    for table_name in TABLE_INSERT_ORDER:
        local_table = local_metadata.tables[table_name]

        # Create new columns with PostgreSQL-compatible types
        new_columns = []
        for col in local_table.columns:
            # Convert SQLite types to PostgreSQL types
            col_type = col.type
            type_str = str(col_type).upper()

            if "DATETIME" in type_str:
                col_type = sa.TIMESTAMP()
            elif "DATE" in type_str:
                col_type = sa.Date()
            elif "DECIMAL" in type_str or "NUMERIC" in type_str:
                col_type = sa.Numeric()
            elif "BOOLEAN" in type_str:
                col_type = sa.Boolean()
            elif isinstance(col_type, sa.TEXT) or "TEXT" in type_str:
                col_type = sa.Text()
            elif (
                isinstance(col_type, sa.INTEGER)
                or "INTEGER" in type_str
                or "INT" in type_str
            ):
                col_type = sa.Integer()
            elif (
                isinstance(col_type, sa.REAL)
                or "REAL" in type_str
                or "FLOAT" in type_str
            ):
                col_type = sa.Float()
            elif isinstance(col_type, sa.BLOB):
                col_type = sa.LargeBinary()
            elif "VARCHAR" in type_str:
                # Use TEXT for all VARCHAR to avoid length issues
                # PostgreSQL TEXT has same performance as VARCHAR
                col_type = sa.Text()

            new_col = sa.Column(
                col.name,
                col_type,
                primary_key=col.primary_key,
                nullable=col.nullable,
            )
            new_columns.append(new_col)

        sa.Table(table_name, remote_metadata, *new_columns)

    # Create all tables
    remote_metadata.create_all(remote_engine)
    log("  All tables created.")

    # Step 5: Identify boolean columns for data conversion
    boolean_columns = {}
    for table_name in TABLE_INSERT_ORDER:
        local_table = local_metadata.tables[table_name]
        bool_cols = []
        for col in local_table.columns:
            type_str = str(col.type).upper()
            if "BOOLEAN" in type_str:
                bool_cols.append(col.name)
        if bool_cols:
            boolean_columns[table_name] = bool_cols

    # Step 6: Insert data into remote database
    log("Inserting data into remote PostgreSQL...")
    summary = {}

    with remote_engine.begin() as conn:
        for table_name in TABLE_INSERT_ORDER:
            table_info = local_data[table_name]
            rows = table_info["rows"]

            if not rows:
                log(f"  {table_name}: 0 rows (empty)")
                summary[table_name] = 0
                continue

            # Convert boolean values (SQLite uses 0/1, PostgreSQL uses true/false)
            if table_name in boolean_columns:
                for row in rows:
                    for col_name in boolean_columns[table_name]:
                        if col_name in row and row[col_name] is not None:
                            row[col_name] = bool(row[col_name])

            # Bulk insert: passing a list of dicts triggers SQLAlchemy's
            # insertmanyvalues, which compiles to multi-row INSERT ... VALUES (...), (...), ...
            # collapsing N round trips into a handful per table.
            remote_table = remote_metadata.tables[table_name]
            conn.execute(remote_table.insert(), rows)

            log(f"  {table_name}: {len(rows)} rows")
            summary[table_name] = len(rows)

    log("Sync completed successfully!")
    return {"success": True, "tables": summary}


def reset_remote_database(verbose: bool = True) -> dict:
    """
    Reset the remote database by syncing from local SQLite.

    This is a convenience function that gets engines from the One singleton.

    Args:
        verbose: If True, print progress messages.

    Returns:
        dict: Summary of the sync operation.
    """
    from labor_ward_ai.one.api import one

    return sync_sqlite_to_postgres(
        local_engine=one.local_sqlite_engine,
        remote_engine=one.remote_postgres_engine,
        verbose=verbose,
    )


def setup_remote_database():
    """Reset database before running tests."""
    print("Resetting database...")
    reset_remote_database(verbose=False)
    print("Database reset complete.\n")

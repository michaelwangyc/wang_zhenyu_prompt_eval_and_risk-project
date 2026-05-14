# -*- coding: utf-8 -*-

"""
Sync local SQLite database to remote PostgreSQL (NeonDB).

This script is idempotent - each run will:
1. DROP all tables in remote database
2. CREATE tables with the same schema
3. INSERT all data from local database
"""

from labor_ward_ai.tests.db_sync import reset_remote_database


def main():
    """Run the sync operation."""
    print("=" * 60)
    print("Syncing local SQLite to remote PostgreSQL (NeonDB)")
    print("=" * 60)

    result = reset_remote_database(verbose=True)

    print("=" * 60)
    print("Summary:")
    for table_name, row_count in result["tables"].items():
        print(f"  {table_name}: {row_count} rows")
    print("=" * 60)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

"""
Download SQLite database file from GitHub Release.

The file will be downloaded to: tmp/data.sqlite
"""

from labor_ward_ai.tests.db_helper import download_sqlite_db

if __name__ == "__main__":
    download_sqlite_db()

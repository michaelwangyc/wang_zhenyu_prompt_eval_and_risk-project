# -*- coding: utf-8 -*-

"""
Database helper functions for testing.

Provides utilities to download and reset the SQLite database for tests.
"""

import urllib.request
from pathlib import Path

from ..paths import path_enum

SQLITE_URL = "https://github.com/easyscale-academy/public-dataset/releases/download/data/healthcare_obstetrics_ward_scheduling_medium.sqlite"


def download_sqlite_db(
    url: str = SQLITE_URL,
    dest: Path = path_enum.path_sqlite_db,
    force: bool = False,
) -> Path:
    """
    Download SQLite database file.

    Args:
        url: URL to download from
        dest: Destination path for the file
        force: If True, always download and overwrite existing file

    Returns:
        Path to the downloaded file
    """
    if dest.exists() and not force:
        print(f"File already exists: {dest}")
        return dest

    # Remove existing file if force download
    if dest.exists():
        dest.unlink()

    # Ensure parent directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {url}")
    print(f"To: {dest}")

    urllib.request.urlretrieve(url, dest)

    print(f"Download complete! File size: {dest.stat().st_size:,} bytes")
    return dest


def reset_test_database() -> Path:
    """
    Reset the test database by deleting and re-downloading.

    This ensures a clean database state before each test run.

    Returns:
        Path to the fresh database file
    """
    dest = path_enum.path_sqlite_db

    # Delete existing file
    if dest.exists():
        dest.unlink()
        print(f"Deleted existing database: {dest}")

    # Download fresh copy
    return download_sqlite_db(force=True)

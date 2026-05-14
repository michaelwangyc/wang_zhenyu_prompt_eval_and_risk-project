# -*- coding: utf-8 -*-

from labor_ward_ai.utils import match


class TestMatch:
    def test_wildcard_include(self):
        """Test wildcard pattern with * for inclusion."""
        assert match("EMPLOYEES", ["EMPLOYEE*"], []) is True
        assert match("EMPLOYEE_HISTORY", ["EMPLOYEE*"], []) is True
        assert match("MANAGERS", ["EMPLOYEE*"], []) is False

    def test_wildcard_exclude(self):
        """Test wildcard pattern for exclusion."""
        assert match("USERS", [], ["*_TEMP", "*_TMP"]) is True
        assert match("USERS_TEMP", [], ["*_TEMP", "*_TMP"]) is False
        assert match("USERS_TMP", [], ["*_TEMP", "*_TMP"]) is False

    def test_regex_include(self):
        """Test regex pattern for inclusion."""
        assert match("EMP_2023", [r"^EMP_\d{4}$"], []) is True
        assert match("EMP_ARCHIVE", [r"^EMP_\d{4}$"], []) is False

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        assert match("employees", ["EMPLOYEES"], []) is True
        assert match("EMPLOYEES", ["employees"], []) is True
        assert match("Employees", ["EMPLOYEES"], []) is True

    def test_empty_include_means_all(self):
        """When include list is empty, all names are included by default."""
        assert match("ANY_TABLE", [], []) is True
        assert match("ANOTHER_TABLE", [], []) is True

    def test_exclude_overrides_include(self):
        """Exclude patterns take precedence over include patterns."""
        assert match("EMPLOYEE_CURRENT", ["EMPLOYEE*", "MANAGER*"], ["*_HISTORY"]) is True
        assert match("EMPLOYEE_HISTORY", ["EMPLOYEE*", "MANAGER*"], ["*_HISTORY"]) is False

    def test_multiple_include_patterns(self):
        """Name must match ANY include pattern (logical OR)."""
        assert match("EMPLOYEES", ["EMPLOYEE*", "MANAGER*"], []) is True
        assert match("MANAGERS", ["EMPLOYEE*", "MANAGER*"], []) is True
        assert match("CUSTOMERS", ["EMPLOYEE*", "MANAGER*"], []) is False

    def test_multiple_exclude_patterns(self):
        """Name must NOT match ANY exclude pattern."""
        assert match("USERS", [], ["*_TEMP", "*_BACKUP", "*_OLD"]) is True
        assert match("USERS_TEMP", [], ["*_TEMP", "*_BACKUP", "*_OLD"]) is False
        assert match("USERS_BACKUP", [], ["*_TEMP", "*_BACKUP", "*_OLD"]) is False
        assert match("USERS_OLD", [], ["*_TEMP", "*_BACKUP", "*_OLD"]) is False


if __name__ == "__main__":
    from labor_ward_ai.tests import run_cov_test

    run_cov_test(
        __file__,
        "labor_ward_ai.utils",
        preview=False,
    )

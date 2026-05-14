# -*- coding: utf-8 -*-

"""
Tests for write_operations module.

Each test:
1. Reads data to find a valid ID
2. Prints the BEFORE state
3. Executes the write operation
4. Reads and prints the AFTER state

Uses a fixture to backup/restore the database file before/after each test.
"""

import shutil
from datetime import datetime, timedelta, UTC

import pytest
import sqlalchemy as sa

from labor_ward_ai.paths import path_enum
from labor_ward_ai.write_operations import (
    assign_bed,
    update_prediction,
    create_alert,
    create_order,
)


@pytest.fixture(autouse=True)
def backup_and_restore_database():
    """
    Fixture that backs up the database before each test and restores it after.

    This ensures each test starts with a clean database state without
    needing to re-download the file.
    """
    db_path = path_enum.path_sqlite_db
    backup_path = db_path.with_suffix(".sqlite.backup")

    # Backup before test
    if db_path.exists():
        shutil.copy2(db_path, backup_path)
        # print(f"\n[FIXTURE] Backed up database to {backup_path}")
    else:
        raise FileNotFoundError(f"Database file not found: {db_path}. Run download first.")

    yield  # Run the test

    # Restore after test
    if backup_path.exists():
        shutil.copy2(backup_path, db_path)
        # print(f"[FIXTURE] Restored database from {backup_path}")
        backup_path.unlink()  # Clean up backup file


@pytest.fixture
def engine():
    """Create and dispose SQLAlchemy engine for the test database."""
    eng = sa.create_engine(f"sqlite:///{path_enum.path_sqlite_db}")
    yield eng
    eng.dispose()


class TestAssignBed:
    def test_assign_bed_to_patient_without_bed(self, engine):
        """Test assigning an available bed to a patient without a bed."""
        print("\n" + "-" * 60)
        print("TEST: assign_bed (patient without bed)")
        print("-" * 60)

        with engine.connect() as conn:
            # Find a patient without a bed (current_bed_id is NULL)
            admission_result = conn.execute(
                sa.text("""
                    SELECT admission_id, current_bed_id, status
                    FROM admission
                    WHERE current_bed_id IS NULL AND status != 'discharged'
                    LIMIT 1
                """)
            )
            admission_row = admission_result.fetchone()

            if admission_row is None:
                # If all patients have beds, create a scenario by clearing one
                admission_result = conn.execute(
                    sa.text("""
                        SELECT admission_id, current_bed_id, status
                        FROM admission
                        WHERE status != 'discharged'
                        LIMIT 1
                    """)
                )
                admission_row = admission_result.fetchone()
                # Clear the bed assignment for testing
                with engine.begin() as tx_conn:
                    if admission_row.current_bed_id:
                        tx_conn.execute(
                            sa.text("UPDATE bed SET status = 'available', current_admission_id = NULL WHERE bed_id = :id"),
                            {"id": admission_row.current_bed_id},
                        )
                        tx_conn.execute(
                            sa.text("UPDATE admission SET current_bed_id = NULL WHERE admission_id = :id"),
                            {"id": admission_row.admission_id},
                        )
                # Re-fetch the admission
                admission_result = conn.execute(
                    sa.text("SELECT admission_id, current_bed_id, status FROM admission WHERE admission_id = :id"),
                    {"id": admission_row.admission_id},
                )
                admission_row = admission_result.fetchone()

            admission_id = admission_row.admission_id
            print(f"\n[TEST] admission_id: {admission_id}")
            print(f"[BEFORE] current_bed_id: {admission_row.current_bed_id}, status: {admission_row.status}")
            assert admission_row.current_bed_id is None, "Patient should have no bed for this test"

            # Find an available bed
            bed_result = conn.execute(
                sa.text("""
                    SELECT bed_id, room_id, bed_label, status
                    FROM bed
                    WHERE status = 'available'
                    LIMIT 1
                """)
            )
            bed_row = bed_result.fetchone()
            assert bed_row is not None, "No available bed found in database"

            bed_id = bed_row.bed_id
            print(f"[TEST] target bed_id: {bed_id}")
            print(f"[BEFORE] bed status: {bed_row.status}")

        # Execute the operation
        result = assign_bed(engine, admission_id, bed_id)
        print(f"[RESULT] {result}")

        # Verify AFTER state
        with engine.connect() as conn:
            admission_after = conn.execute(
                sa.text("SELECT current_bed_id FROM admission WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[AFTER] admission.current_bed_id: {admission_after.current_bed_id}")

            bed_after = conn.execute(
                sa.text("SELECT status, current_admission_id FROM bed WHERE bed_id = :id"),
                {"id": bed_id},
            ).fetchone()
            print(f"[AFTER] bed.status: {bed_after.status}, bed.current_admission_id: {bed_after.current_admission_id}")

        assert result["success"] is True
        assert admission_after.current_bed_id == bed_id
        assert bed_after.status == "occupied"
        assert bed_after.current_admission_id == admission_id

        print("-" * 60)

    def test_transfer_patient_to_different_bed(self, engine):
        """Test transferring a patient from one bed to another."""
        print("\n" + "-" * 60)
        print("TEST: assign_bed (transfer)")
        print("-" * 60)

        with engine.connect() as conn:
            # Find a patient WITH a bed
            admission_result = conn.execute(
                sa.text("""
                    SELECT admission_id, current_bed_id, status
                    FROM admission
                    WHERE current_bed_id IS NOT NULL AND status != 'discharged'
                    LIMIT 1
                """)
            )
            admission_row = admission_result.fetchone()
            assert admission_row is not None, "No patient with bed found"

            admission_id = admission_row.admission_id
            old_bed_id = admission_row.current_bed_id
            print(f"\n[TEST] admission_id: {admission_id}")
            print(f"[BEFORE] old_bed_id: {old_bed_id}, status: {admission_row.status}")

            # Find a DIFFERENT available bed
            bed_result = conn.execute(
                sa.text("""
                    SELECT bed_id, bed_label, status
                    FROM bed
                    WHERE status = 'available' AND bed_id != :old_bed_id
                    LIMIT 1
                """),
                {"old_bed_id": old_bed_id},
            )
            new_bed_row = bed_result.fetchone()
            assert new_bed_row is not None, "No other available bed found"

            new_bed_id = new_bed_row.bed_id
            print(f"[TEST] new_bed_id: {new_bed_id}")

        # Execute the transfer
        result = assign_bed(engine, admission_id, new_bed_id)
        print(f"[RESULT] {result}")

        # Verify AFTER state
        with engine.connect() as conn:
            # Check admission has new bed
            admission_after = conn.execute(
                sa.text("SELECT current_bed_id FROM admission WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[AFTER] admission.current_bed_id: {admission_after.current_bed_id}")

            # Check old bed is now available
            old_bed_after = conn.execute(
                sa.text("SELECT status, current_admission_id FROM bed WHERE bed_id = :id"),
                {"id": old_bed_id},
            ).fetchone()
            print(f"[AFTER] old_bed.status: {old_bed_after.status}, old_bed.current_admission_id: {old_bed_after.current_admission_id}")

            # Check new bed is occupied
            new_bed_after = conn.execute(
                sa.text("SELECT status, current_admission_id FROM bed WHERE bed_id = :id"),
                {"id": new_bed_id},
            ).fetchone()
            print(f"[AFTER] new_bed.status: {new_bed_after.status}, new_bed.current_admission_id: {new_bed_after.current_admission_id}")

        assert result["success"] is True
        assert admission_after.current_bed_id == new_bed_id
        assert old_bed_after.status == "available"
        assert old_bed_after.current_admission_id is None
        assert new_bed_after.status == "occupied"
        assert new_bed_after.current_admission_id == admission_id

        print("-" * 60)

    def test_assign_occupied_bed_raises_error(self, engine):
        """Test that assigning an occupied bed raises ValueError."""
        print("\n" + "-" * 60)
        print("TEST: assign_bed (occupied bed should fail)")
        print("-" * 60)

        with engine.connect() as conn:
            # Find a patient
            admission_result = conn.execute(
                sa.text("""
                    SELECT admission_id, current_bed_id
                    FROM admission
                    WHERE status != 'discharged'
                    LIMIT 1
                """)
            )
            admission_row = admission_result.fetchone()
            assert admission_row is not None

            admission_id = admission_row.admission_id

            # Find an OCCUPIED bed (different from patient's current bed if any)
            bed_result = conn.execute(
                sa.text("""
                    SELECT bed_id, status, current_admission_id
                    FROM bed
                    WHERE status = 'occupied' AND bed_id != COALESCE(:current_bed_id, '')
                    LIMIT 1
                """),
                {"current_bed_id": admission_row.current_bed_id},
            )
            occupied_bed = bed_result.fetchone()
            assert occupied_bed is not None, "No occupied bed found"

            print(f"[TEST] admission_id: {admission_id}")
            print(f"[TEST] occupied_bed_id: {occupied_bed.bed_id}, status: {occupied_bed.status}")

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            assign_bed(engine, admission_id, occupied_bed.bed_id)

        print(f"[RESULT] Correctly raised ValueError: {exc_info.value}")
        assert "not available" in str(exc_info.value)

        print("-" * 60)


class TestUpdatePrediction:
    def test_update_prediction_for_admission(self, engine):
        """Test updating length-of-stay prediction for an admission."""
        print("\n" + "-" * 60)
        print("TEST: update_prediction")
        print("-" * 60)

        with engine.connect() as conn:
            # Find an admission that is not discharged
            admission_result = conn.execute(
                sa.text("""
                    SELECT admission_id, status, admit_time, predicted_los_hours, predicted_discharge_time
                    FROM admission
                    WHERE status != 'discharged'
                    LIMIT 1
                """)
            )
            admission_row = admission_result.fetchone()
            assert admission_row is not None, "No active admission found"

            admission_id = admission_row.admission_id
            print(f"\n[TEST] admission_id: {admission_id}")
            print(f"[BEFORE] status: {admission_row.status}")
            print(f"[BEFORE] predicted_los_hours: {admission_row.predicted_los_hours}")
            print(f"[BEFORE] predicted_discharge_time: {admission_row.predicted_discharge_time}")

        # New prediction values
        new_los_hours = 72
        new_discharge_time = datetime.now(UTC) + timedelta(hours=new_los_hours)
        print(f"[TEST] new_los_hours: {new_los_hours}")
        print(f"[TEST] new_discharge_time: {new_discharge_time}")

        # Execute the operation
        result = update_prediction(engine, admission_id, new_los_hours, new_discharge_time)
        print(f"[RESULT] {result}")

        # Verify AFTER state
        with engine.connect() as conn:
            admission_after = conn.execute(
                sa.text("SELECT predicted_los_hours, predicted_discharge_time FROM admission WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[AFTER] predicted_los_hours: {admission_after.predicted_los_hours}")
            print(f"[AFTER] predicted_discharge_time: {admission_after.predicted_discharge_time}")

        assert result["success"] is True
        assert admission_after.predicted_los_hours == new_los_hours

        print("-" * 60)


class TestCreateAlert:
    def test_create_alert_for_admission(self, engine):
        """Test creating a high-risk alert for an admission."""
        print("\n" + "-" * 60)
        print("TEST: create_alert")
        print("-" * 60)

        with engine.connect() as conn:
            # Find an admission that is not discharged
            admission_result = conn.execute(
                sa.text("""
                    SELECT admission_id, status
                    FROM admission
                    WHERE status != 'discharged'
                    LIMIT 1
                """)
            )
            admission_row = admission_result.fetchone()
            assert admission_row is not None, "No active admission found"

            admission_id = admission_row.admission_id
            print(f"\n[TEST] admission_id: {admission_id}")
            print(f"[BEFORE] status: {admission_row.status}")

            # Count existing alerts for this admission
            alert_count_before = conn.execute(
                sa.text("SELECT COUNT(*) as cnt FROM alert WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[BEFORE] alert count for this admission: {alert_count_before.cnt}")

        # Create alert
        alert_type = "high_bp"
        severity = "warning"
        message = "Test alert: BP trending upward 130 -> 138 -> 145"
        print(f"[TEST] alert_type: {alert_type}, severity: {severity}")

        # Execute the operation
        result = create_alert(engine, admission_id, alert_type, severity, message)
        print(f"[RESULT] {result}")

        # Verify AFTER state
        with engine.connect() as conn:
            alert_count_after = conn.execute(
                sa.text("SELECT COUNT(*) as cnt FROM alert WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[AFTER] alert count for this admission: {alert_count_after.cnt}")

            # Verify the new alert exists
            new_alert = conn.execute(
                sa.text("SELECT alert_id, alert_type, severity, message, acknowledged FROM alert WHERE alert_id = :id"),
                {"id": result["alert_id"]},
            ).fetchone()
            print(f"[AFTER] new alert_id: {new_alert.alert_id}")
            print(f"[AFTER] alert_type: {new_alert.alert_type}, severity: {new_alert.severity}")
            print(f"[AFTER] acknowledged: {new_alert.acknowledged}")

        assert result["success"] is True
        assert "alert_id" in result
        assert alert_count_after.cnt == alert_count_before.cnt + 1
        assert new_alert.alert_type == alert_type
        assert new_alert.severity == severity
        assert new_alert.acknowledged in (False, 0)  # SQLite returns 0 for boolean false

        print("-" * 60)


class TestCreateOrder:
    def test_create_order_for_admission(self, engine):
        """Test creating a medical order for an admission."""
        print("\n" + "-" * 60)
        print("TEST: create_order")
        print("-" * 60)

        with engine.connect() as conn:
            # Find an admission that is not discharged
            admission_result = conn.execute(
                sa.text("""
                    SELECT admission_id, status
                    FROM admission
                    WHERE status != 'discharged'
                    LIMIT 1
                """)
            )
            admission_row = admission_result.fetchone()
            assert admission_row is not None, "No active admission found"

            admission_id = admission_row.admission_id
            print(f"\n[TEST] admission_id: {admission_id}")
            print(f"[BEFORE] admission status: {admission_row.status}")

            # Find a provider
            provider_result = conn.execute(
                sa.text("SELECT provider_id, name, role FROM provider LIMIT 1")
            )
            provider_row = provider_result.fetchone()
            assert provider_row is not None, "No provider found"

            provider_id = provider_row.provider_id
            print(f"[TEST] provider_id: {provider_id}, name: {provider_row.name}, role: {provider_row.role}")

            # Count existing orders for this admission
            order_count_before = conn.execute(
                sa.text("SELECT COUNT(*) as cnt FROM medical_order WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[BEFORE] order count for this admission: {order_count_before.cnt}")

        # Create order
        order_type = "lab_test"
        scheduled_time = datetime.now(UTC) + timedelta(hours=2)
        priority = "routine"
        print(f"[TEST] order_type: {order_type}, scheduled_time: {scheduled_time}, priority: {priority}")

        # Execute the operation
        result = create_order(
            engine,
            admission_id,
            order_type,
            scheduled_time,
            provider_id,
            priority=priority,
            notes="Test order for unit test",
        )
        print(f"[RESULT] {result}")

        # Verify AFTER state
        with engine.connect() as conn:
            order_count_after = conn.execute(
                sa.text("SELECT COUNT(*) as cnt FROM medical_order WHERE admission_id = :id"),
                {"id": admission_id},
            ).fetchone()
            print(f"[AFTER] order count for this admission: {order_count_after.cnt}")

            # Verify the new order exists
            new_order = conn.execute(
                sa.text("""
                    SELECT order_id, order_type, status, priority, created_by
                    FROM medical_order
                    WHERE order_id = :id
                """),
                {"id": result["order_id"]},
            ).fetchone()
            print(f"[AFTER] new order_id: {new_order.order_id}")
            print(f"[AFTER] order_type: {new_order.order_type}, status: {new_order.status}")
            print(f"[AFTER] priority: {new_order.priority}, created_by: {new_order.created_by}")

        assert result["success"] is True
        assert "order_id" in result
        assert order_count_after.cnt == order_count_before.cnt + 1
        assert new_order.order_type == order_type
        assert new_order.status == "scheduled"
        assert new_order.created_by == "ai_assisted"

        print("-" * 60)


if __name__ == "__main__":
    from labor_ward_ai.tests import run_cov_test

    run_cov_test(
        __file__,
        "labor_ward_ai.write_operations",
        preview=False,
    )

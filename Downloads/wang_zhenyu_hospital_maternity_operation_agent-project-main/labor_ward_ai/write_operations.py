# -*- coding: utf-8 -*-

"""
Database write operations for MaterniFlow.

Each function takes an SQLAlchemy engine and scalar parameters.
All operations use transactions and parameterized queries to prevent SQL injection.
Errors are raised as exceptions.
"""

import typing as T
import uuid
from datetime import datetime, UTC

import sqlalchemy as sa


def assign_bed(
    engine: "sa.Engine",
    admission_id: str,
    bed_id: str,
) -> dict:
    """
    Assign or transfer a patient to a bed.

    This operation:
    1. If patient has an existing bed (transfer case): release the old bed
    2. Update the new bed: status -> 'occupied', current_admission_id -> admission_id
    3. Update admission: current_bed_id -> bed_id

    Example scenario (from design doc - Scene 2: Room Scheduling):
        Nurse: "Emergency just came in with a patient in labor, any available labor rooms?"
        Agent: "Labor rooms are full. But patient Wang in room 203 is already at 8cm dilation,
                expected to move to delivery room in 1-2 hours. Room 205's patient Zhao just
                started induction today, won't be available soon. Suggest temporary triage area,
                prioritize waiting for 203. Should I assign triage-01 to the new patient now?"
        Nurse: "Yes."
        Agent: calls assign_bed(admission_id=new_patient_id, bed_id=triage_01_id)

    :param engine: SQLAlchemy engine instance.
    :param admission_id: UUID of the admission record.
    :param bed_id: UUID of the target bed.
    :return: dict with success status and message.
    :raises ValueError: If admission or bed not found, or bed not available.
    """
    with engine.begin() as conn:
        # Check if admission exists
        admission_result = conn.execute(
            sa.text("SELECT admission_id, current_bed_id FROM admission WHERE admission_id = :admission_id"),
            {"admission_id": admission_id},
        )
        admission_row = admission_result.fetchone()
        if admission_row is None:
            raise ValueError(f"Admission not found: {admission_id}")

        old_bed_id = admission_row.current_bed_id

        # Check if target bed exists and is available
        bed_result = conn.execute(
            sa.text("SELECT bed_id, status FROM bed WHERE bed_id = :bed_id"),
            {"bed_id": bed_id},
        )
        bed_row = bed_result.fetchone()
        if bed_row is None:
            raise ValueError(f"Bed not found: {bed_id}")
        if bed_row.status != "available":
            raise ValueError(f"Bed is not available: {bed_id} (status: {bed_row.status})")

        # If patient has old bed, release it
        if old_bed_id is not None:
            conn.execute(
                sa.text("""
                    UPDATE bed
                    SET status = 'available', current_admission_id = NULL
                    WHERE bed_id = :old_bed_id
                """),
                {"old_bed_id": old_bed_id},
            )

        # Assign new bed
        conn.execute(
            sa.text("""
                UPDATE bed
                SET status = 'occupied', current_admission_id = :admission_id
                WHERE bed_id = :bed_id
            """),
            {"admission_id": admission_id, "bed_id": bed_id},
        )

        # Update admission
        conn.execute(
            sa.text("UPDATE admission SET current_bed_id = :bed_id WHERE admission_id = :admission_id"),
            {"bed_id": bed_id, "admission_id": admission_id},
        )

    return {"success": True, "message": f"Assigned admission {admission_id} to bed {bed_id}"}


def update_prediction(
    engine: "sa.Engine",
    admission_id: str,
    predicted_los_hours: int,
    predicted_discharge_time: datetime,
) -> dict:
    """
    Update the length-of-stay prediction for an admission.

    Example scenario (from design doc - Scene 3: Length of Stay Prediction):
        Nurse: "Patient Chen in room 203 just had a C-section, when can she be discharged?"
        Agent: "Chen just completed C-section, first baby, no complications. Based on her
                condition, expected discharge on day 3 post-op, which is Thursday.
                I've updated the predicted discharge time in the system."
        Agent: calls update_prediction(
            admission_id=chen_admission_id,
            predicted_los_hours=72,
            predicted_discharge_time=thursday_10am
        )

    :param engine: SQLAlchemy engine instance.
    :param admission_id: UUID of the admission record.
    :param predicted_los_hours: Predicted length of stay in hours (must be 6-336).
    :param predicted_discharge_time: Predicted discharge datetime.
    :return: dict with success status and message.
    :raises ValueError: If admission not found, already discharged, or prediction out of range.
    """
    # Validate prediction range (6 hours to 14 days)
    if not (6 <= predicted_los_hours <= 336):
        raise ValueError(f"Predicted LOS hours must be between 6 and 336, got: {predicted_los_hours}")

    with engine.begin() as conn:
        # Check admission exists and not discharged
        admission_result = conn.execute(
            sa.text("SELECT admission_id, status, admit_time FROM admission WHERE admission_id = :admission_id"),
            {"admission_id": admission_id},
        )
        admission_row = admission_result.fetchone()
        if admission_row is None:
            raise ValueError(f"Admission not found: {admission_id}")
        if admission_row.status == "discharged":
            raise ValueError(f"Cannot update prediction for discharged admission: {admission_id}")

        # Validate discharge time is after admit time
        # Handle admit_time as string (SQLite) or datetime
        admit_time = admission_row.admit_time
        if isinstance(admit_time, str):
            admit_time = datetime.fromisoformat(admit_time)

        # Compare as naive datetimes (remove timezone info if present)
        discharge_naive = predicted_discharge_time.replace(tzinfo=None) if predicted_discharge_time.tzinfo else predicted_discharge_time
        admit_naive = admit_time.replace(tzinfo=None) if admit_time.tzinfo else admit_time
        if discharge_naive <= admit_naive:
            raise ValueError("Predicted discharge time must be after admit time")

        # Update prediction
        conn.execute(
            sa.text("""
                UPDATE admission
                SET predicted_los_hours = :los_hours, predicted_discharge_time = :discharge_time
                WHERE admission_id = :admission_id
            """),
            {
                "los_hours": predicted_los_hours,
                "discharge_time": predicted_discharge_time,
                "admission_id": admission_id,
            },
        )

    return {"success": True, "message": f"Updated prediction for admission {admission_id}"}


def create_alert(
    engine: "sa.Engine",
    admission_id: str,
    alert_type: str,
    severity: str,
    message: str,
) -> dict:
    """
    Create a high-risk alert for an admission.

    Example scenario (from design doc - Scene 4: High-Risk Alert):
        Nurse: "Who needs special attention today?"
        Agent: "Two patients to watch: Liu has gestational hypertension, BP trending up
                this morning (130 -> 138 -> 145), recommend increased monitoring frequency.
                Zhou has twins at 34 weeks, preterm risk, NICU confirmed 2 beds available.
                I've created alert records for both."
        Agent: calls create_alert(
            admission_id=liu_admission_id,
            alert_type="high_bp",
            severity="warning",
            message="Systolic BP rising trend over 3 readings: 130 -> 138 -> 145, recommend increased monitoring"
        )

    :param engine: SQLAlchemy engine instance.
    :param admission_id: UUID of the admission record.
    :param alert_type: Type of alert (high_bp, abnormal_fhr, fever, preterm_risk).
    :param severity: Severity level (warning, critical).
    :param message: Alert message describing the situation.
    :return: dict with success status, message, and alert_id.
    :raises ValueError: If admission not found, not in hospital, or invalid alert_type/severity.
    """
    valid_alert_types = {"high_bp", "abnormal_fhr", "fever", "preterm_risk"}
    valid_severities = {"warning", "critical"}

    if alert_type not in valid_alert_types:
        raise ValueError(f"Invalid alert_type: {alert_type}. Must be one of {valid_alert_types}")
    if severity not in valid_severities:
        raise ValueError(f"Invalid severity: {severity}. Must be one of {valid_severities}")

    with engine.begin() as conn:
        # Check admission exists and patient is still in hospital
        admission_result = conn.execute(
            sa.text("SELECT admission_id, status FROM admission WHERE admission_id = :admission_id"),
            {"admission_id": admission_id},
        )
        admission_row = admission_result.fetchone()
        if admission_row is None:
            raise ValueError(f"Admission not found: {admission_id}")
        if admission_row.status == "discharged":
            raise ValueError(f"Cannot create alert for discharged patient: {admission_id}")

        # Generate new alert_id
        alert_id = str(uuid.uuid4())
        triggered_at = datetime.now(UTC)

        # Insert alert
        conn.execute(
            sa.text("""
                INSERT INTO alert (alert_id, admission_id, alert_type, severity, message, triggered_at, acknowledged)
                VALUES (:alert_id, :admission_id, :alert_type, :severity, :message, :triggered_at, :acknowledged)
            """),
            {
                "alert_id": alert_id,
                "admission_id": admission_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "triggered_at": triggered_at,
                "acknowledged": False,
            },
        )

    return {"success": True, "message": f"Created alert {alert_id}", "alert_id": alert_id}


def create_order(
    engine: "sa.Engine",
    admission_id: str,
    order_type: str,
    scheduled_time: datetime,
    assigned_provider_id: str,
    priority: str = "routine",
    assigned_room_id: T.Optional[str] = None,
    notes: str = "",
) -> dict:
    """
    Create a medical order (surgery, procedure, lab test, etc.).

    Example scenario (from design doc - Scene 5: Place Medical Order):
        Nurse: "Schedule a C-section for patient Wang in room 203 tomorrow morning."
        Agent: "Let me check tomorrow's day shift schedule: Dr. Smith (surgeon) and
                Dr. Lee (anesthesiologist) are both available. Delivery room 1 is open
                9-11am tomorrow. Schedule for 9am tomorrow, delivery room 1?"
        Nurse: "Yes."
        Agent: calls create_order(
            admission_id=wang_admission_id,
            order_type="c_section",
            scheduled_time=tomorrow_9am,
            assigned_provider_id=dr_smith_id,
            assigned_room_id=delivery_room_1_id,
            priority="routine"
        )
        Agent: "Scheduled. Surgeon Dr. Smith, Anesthesiologist Dr. Lee, tomorrow 9am,
                delivery room 1. Should I also notify the anesthesiology department?"

    :param engine: SQLAlchemy engine instance.
    :param admission_id: UUID of the admission record.
    :param order_type: Type of order (c_section, induction, epidural, lab_test, medication, consult).
    :param scheduled_time: Scheduled datetime for the order.
    :param assigned_provider_id: UUID of the provider assigned to execute the order.
    :param priority: Priority level (routine, urgent, emergency). Default: routine.
    :param assigned_room_id: UUID of the room (optional, required for surgeries).
    :param notes: Additional notes.
    :return: dict with success status, message, and order_id.
    :raises ValueError: If admission/provider not found, or invalid order_type/priority.
    """
    valid_order_types = {"c_section", "induction", "epidural", "lab_test", "medication", "consult"}
    valid_priorities = {"routine", "urgent", "emergency"}

    if order_type not in valid_order_types:
        raise ValueError(f"Invalid order_type: {order_type}. Must be one of {valid_order_types}")
    if priority not in valid_priorities:
        raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")

    with engine.begin() as conn:
        # Check admission exists and patient is still in hospital
        admission_result = conn.execute(
            sa.text("SELECT admission_id, status FROM admission WHERE admission_id = :admission_id"),
            {"admission_id": admission_id},
        )
        admission_row = admission_result.fetchone()
        if admission_row is None:
            raise ValueError(f"Admission not found: {admission_id}")
        if admission_row.status == "discharged":
            raise ValueError(f"Cannot create order for discharged patient: {admission_id}")

        # Check provider exists
        provider_result = conn.execute(
            sa.text("SELECT provider_id FROM provider WHERE provider_id = :provider_id"),
            {"provider_id": assigned_provider_id},
        )
        if provider_result.fetchone() is None:
            raise ValueError(f"Provider not found: {assigned_provider_id}")

        # Check room exists if provided
        if assigned_room_id is not None:
            room_result = conn.execute(
                sa.text("SELECT room_id FROM room WHERE room_id = :room_id"),
                {"room_id": assigned_room_id},
            )
            if room_result.fetchone() is None:
                raise ValueError(f"Room not found: {assigned_room_id}")

        # Generate new order_id
        order_id = str(uuid.uuid4())

        # Insert order
        conn.execute(
            sa.text("""
                INSERT INTO medical_order
                (order_id, admission_id, order_type, status, scheduled_time,
                 assigned_provider_id, assigned_room_id, priority, notes, created_by)
                VALUES
                (:order_id, :admission_id, :order_type, :status, :scheduled_time,
                 :assigned_provider_id, :assigned_room_id, :priority, :notes, :created_by)
            """),
            {
                "order_id": order_id,
                "admission_id": admission_id,
                "order_type": order_type,
                "status": "scheduled",
                "scheduled_time": scheduled_time,
                "assigned_provider_id": assigned_provider_id,
                "assigned_room_id": assigned_room_id,
                "priority": priority,
                "notes": notes,
                "created_by": "ai_assisted",
            },
        )

    return {"success": True, "message": f"Created order {order_id}", "order_id": order_id}

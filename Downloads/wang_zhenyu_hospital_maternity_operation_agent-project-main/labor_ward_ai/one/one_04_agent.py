# -*- coding: utf-8 -*-

"""AI Agent mixin for the One class."""

import json
import typing as T
from datetime import datetime
from functools import cached_property

from strands import Agent, tool
from strands.models import BedrockModel

from ..paths import path_enum
from .. import write_operations

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class AgentMixin:
    """Mixin providing AI agent and tool definitions for database queries."""

    @cached_property
    def bedrock_model(self: "One") -> BedrockModel:
        """Create a BedrockModel instance with configured model ID."""
        return BedrockModel(
            boto_session=self.boto_ses,
            model_id=self.config.model_id,
        )

    @cached_property
    def model(self: "One"):
        """Get the model instance (alias for bedrock_model)."""
        return self.bedrock_model

    @cached_property
    def agent(self: "One") -> Agent:
        """Create an Agent instance with the configured model."""
        return Agent(
            model=self.model,
            system_prompt=path_enum.path_bi_agent_system_prompt_content,
            tools=[
                # Read-only tools
                self.tool_get_database_schema,
                self.tool_execute_sql_query,
                self.tool_write_debug_report,
                # Write operation tools
                self.tool_assign_bed,
                self.tool_update_prediction,
                self.tool_create_alert,
                self.tool_create_order,
            ],
        )

    @tool(
        name="get_database_schema",
    )
    def tool_get_database_schema(
        # self: "One",  # keep for IDE type hints, strands @tool doesn't support typed self
        self,  # uncomment this and comment above when running with strands
    ) -> str:
        """
        Retrieve the complete database schema information in LLM-optimized compact format.

        This tool returns the structure of all tables in the healthcare obstetrics ward
        scheduling database, including:
        - Table names and column definitions
        - Data types (simplified to STR, INT, DEC, TS, DT, etc.)
        - Constraints: Primary Key (*PK), Unique (*UQ), Not Null (*NN), Index (*IDX)
        - Foreign key relationships (*FK->Table.Column)

        Use this tool FIRST to understand the database structure before writing SQL queries.
        The compact format reduces token usage by ~70% compared to verbose SQL DDL.

        Returns:
            A string containing the encoded database schema in compact format.
        """
        return self.database_schema_str

    @tool(
        name="execute_sql_query",
    )
    def tool_execute_sql_query(
        # self: "One",  # keep for IDE type hints, strands @tool doesn't support typed self
        self,  # uncomment this and comment above when running with strands
        sql: str,
    ) -> str:
        """
        Execute a SQL SELECT query and return results as a Markdown table.

        This tool runs the provided SQL query against the healthcare obstetrics ward
        scheduling database and returns the results formatted as a Markdown table.
        Markdown tables are token-efficient (~24% fewer tokens than JSON) and
        easy for LLMs to parse.

        Args:
            sql: A valid SQL SELECT query string to execute.

        Returns:
            - On success: A Markdown-formatted table with query results
            - If no rows match: "No result"
            - On error: An error message describing what went wrong

        Note:
            Only SELECT queries are supported. Use get_database_schema first to
            understand available tables and columns before constructing queries.
        """
        return self.execute_and_print_result(sql=sql)


    @tool(
        name="write_debug_report",
    )
    def tool_write_debug_report(
        self,
        content: str,
    ) -> str:
        """
        Write a debug report documenting the reasoning process and intermediate steps.

        This tool writes a markdown report to tmp/debug_report.md for debugging and
        transparency purposes. Use this to document your reasoning process.

        Args:
            content: The full markdown content to write to the debug report file.
                     Should include sections like:
                     - User Question
                     - Schema Analysis
                     - SQL Queries and Results
                     - Reasoning Steps
                     - Final Answer

        Returns:
            A confirmation message with the file path.
        """
        try:
            path_enum.path_debug_report_md.write_text(content, encoding="utf-8")
        except FileNotFoundError:
            path_enum.dir_tmp.mkdir(parents=True, exist_ok=True)
            path_enum.path_debug_report_md.write_text(content, encoding="utf-8")
        return f"Debug report written to: {path_enum.path_debug_report_md}"

    # =========================================================================
    # Write Operation Tools
    # =========================================================================

    @tool(name="assign_bed")
    def tool_assign_bed(
        self,
        admission_id: str,
        bed_id: str,
    ) -> str:
        """
        Assign or transfer a patient to a bed.

        Use this tool when:
        - A new patient needs to be assigned to an available bed
        - A patient needs to be transferred to a different bed
        - Nurse says things like "assign patient X to bed Y" or "move patient to room Z"

        The tool will:
        1. Release the patient's old bed (if any)
        2. Mark the new bed as occupied
        3. Update the admission record with the new bed

        Args:
            admission_id: The UUID of the admission record (patient's current stay).
            bed_id: The UUID of the target bed to assign.

        Returns:
            JSON string with success status and message, or error details.

        Example user requests that trigger this tool:
        - "Assign the new patient to bed 101-A"
        - "Transfer patient Wang to triage area"
        - "Move the patient in room 203 to delivery room 1"
        """
        try:
            result = write_operations.assign_bed(
                engine=self.engine,
                admission_id=admission_id,
                bed_id=bed_id,
            )
            return json.dumps(result)
        except ValueError as e:
            return json.dumps({"success": False, "error": str(e)})

    @tool(name="update_prediction")
    def tool_update_prediction(
        self,
        admission_id: str,
        predicted_los_hours: int,
        predicted_discharge_time: str,
    ) -> str:
        """
        Update the length-of-stay (LOS) prediction for a patient.

        Use this tool when:
        - Updating discharge time estimates after clinical assessment
        - Adjusting LOS prediction based on patient progress
        - Nurse asks "when can patient X be discharged?" and you provide an estimate

        Args:
            admission_id: The UUID of the admission record.
            predicted_los_hours: Predicted length of stay in hours (must be 6-336, i.e., 6 hours to 14 days).
            predicted_discharge_time: Predicted discharge datetime in ISO format (e.g., "2024-01-15T10:00:00").

        Returns:
            JSON string with success status and message, or error details.

        Example user requests that trigger this tool:
        - "Patient Chen just had a C-section, estimate discharge in 3 days"
        - "Update the discharge prediction for room 205 to Friday morning"
        - "The patient is recovering well, she can go home in 48 hours"
        """
        try:
            discharge_dt = datetime.fromisoformat(predicted_discharge_time)
            result = write_operations.update_prediction(
                engine=self.engine,
                admission_id=admission_id,
                predicted_los_hours=predicted_los_hours,
                predicted_discharge_time=discharge_dt,
            )
            return json.dumps(result)
        except ValueError as e:
            return json.dumps({"success": False, "error": str(e)})

    @tool(name="create_alert")
    def tool_create_alert(
        self,
        admission_id: str,
        alert_type: str,
        severity: str,
        message: str,
    ) -> str:
        """
        Create a high-risk alert for a patient.

        Use this tool when:
        - Detecting abnormal vital signs or trends
        - Identifying high-risk conditions that need attention
        - Nurse asks about patients who need special monitoring

        Args:
            admission_id: The UUID of the admission record.
            alert_type: Type of alert. Must be one of: "high_bp", "abnormal_fhr", "fever", "preterm_risk".
            severity: Severity level. Must be one of: "warning", "critical".
            message: Descriptive message explaining the alert (e.g., "BP rising trend: 130 -> 138 -> 145").

        Returns:
            JSON string with success status, message, and alert_id, or error details.

        Example user requests that trigger this tool:
        - "Patient Liu's blood pressure is trending up, create an alert"
        - "Flag patient Zhou as high-risk for preterm delivery"
        - "The fetal heart rate is abnormal, we need to monitor closely"
        """
        try:
            result = write_operations.create_alert(
                engine=self.engine,
                admission_id=admission_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
            )
            return json.dumps(result)
        except ValueError as e:
            return json.dumps({"success": False, "error": str(e)})

    @tool(name="create_order")
    def tool_create_order(
        self,
        admission_id: str,
        order_type: str,
        scheduled_time: str,
        assigned_provider_id: str,
        priority: str = "routine",
        assigned_room_id: T.Optional[str] = None,
        notes: str = "",
    ) -> str:
        """
        Create a medical order (surgery, procedure, lab test, etc.).

        Use this tool when:
        - Scheduling a C-section or other surgery
        - Ordering lab tests or procedures
        - Nurse says "schedule X for patient Y"

        Args:
            admission_id: The UUID of the admission record.
            order_type: Type of order. Must be one of: "c_section", "induction", "epidural", "lab_test", "medication", "consult".
            scheduled_time: Scheduled datetime in ISO format (e.g., "2024-01-15T09:00:00").
            assigned_provider_id: The UUID of the provider who will execute the order.
            priority: Priority level. Must be one of: "routine", "urgent", "emergency". Default: "routine".
            assigned_room_id: The UUID of the room (optional, but required for surgeries like c_section).
            notes: Additional notes (optional).

        Returns:
            JSON string with success status, message, and order_id, or error details.

        Example user requests that trigger this tool:
        - "Schedule a C-section for patient Wang tomorrow at 9am"
        - "Order an epidural for the patient in room 203"
        - "Schedule a lab test for patient Chen"
        """
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
            result = write_operations.create_order(
                engine=self.engine,
                admission_id=admission_id,
                order_type=order_type,
                scheduled_time=scheduled_dt,
                assigned_provider_id=assigned_provider_id,
                priority=priority,
                assigned_room_id=assigned_room_id,
                notes=notes,
            )
            return json.dumps(result)
        except ValueError as e:
            return json.dumps({"success": False, "error": str(e)})

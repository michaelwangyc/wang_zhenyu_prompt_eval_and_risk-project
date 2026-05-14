# -*- coding: utf-8 -*-

"""
Test script for the BI Agent.

Usage:
    .venv/bin/python scripts/test_one.py

Change the `request` variable at the bottom to test different queries.
"""

from labor_ward_ai.one.api import one

# =============================================================================
# Test Requests - Onboarding & System Understanding (1-3)
# =============================================================================

# Understanding system capabilities
request_01 = """
What can you help me with? What are your main capabilities?
""".strip()

# Understanding database entities and relationships
request_02 = """
Can you explain the main entities in this database and how they relate to each other?
""".strip()

# Understanding the admission workflow
request_03 = """
What does the patient admission workflow look like? What statuses can an admission go through?
""".strip()

# =============================================================================
# Test Requests - Simple Queries (4-6)
# =============================================================================

# Simple count query
request_04 = """
How many patients are currently in the ward? Break it down by admission status.
""".strip()

# Simple filter query
request_05 = """
Which beds are currently available? Show me the room number, bed label, and room type.
""".strip()

# Simple date filter query
request_06 = """
Show me today's scheduled procedures. Include the patient name, procedure type, and scheduled time.
""".strip()

# =============================================================================
# Test Requests - Medium Complexity (7-8)
# =============================================================================

# Join with filtering on risk factors
request_07 = """
Who are the high-risk patients currently admitted? Show their names, gestational weeks, risk level, and any complications they have.
""".strip()

# Aggregation with grouping
request_08 = """
What's the bed occupancy rate for each room type? Show total beds, occupied beds, and occupancy percentage.
""".strip()

# =============================================================================
# Test Requests - Complex Multi-Step Queries (9-10)
# =============================================================================

# Multiple joins + time calculation
request_09 = """
For patients currently in labor, show me their latest labor progress (cervical dilation, station) and how long they've been in labor since admission.
""".strip()

# Comprehensive summary requiring multiple queries
request_10 = """
Give me a shift handover summary:
1. Current patient census grouped by admission status
2. Any unacknowledged alerts
3. Upcoming scheduled procedures in the next 24 hours
4. Any high-risk patients I should pay special attention to
""".strip()

# =============================================================================
# Run the selected request
# =============================================================================

# Change this to test different requests (request_01 to request_10)
request = request_10

one.agent(request)
# Database Table Walkthrough

This guide walks you through the SMB Lending Lens database from a business perspective. We'll start with the simplest tables and work our way up to the more complex relationships.

---

## Business Context

**Pacific Bridge Lending** is a mid-sized fintech company based in California that specializes in small-to-medium business (SMB) loans.

**Core Business Flow:**

```
Business Customer → Submit Application → Credit Review → Disburse Loan → Monthly Payments → Payoff / Default
```

**Data Scale:**

- 10 tables, ~52,000 records
- 12 foreign key relationships
- Covers approximately 2 years of operations

---

## Table Dependencies (Simple to Complex)

Tables are ordered by dependency count, so you can build understanding progressively:

| Tier | Table | Records | Dependencies | Description |
|------|-------|---------|--------------|-------------|
| **Tier 1: Lookup Tables** | | | | |
| 1 | `industry` | 15 | None | Industry classifications |
| 2 | `risk_grade` | 5 | None | Risk tiers (A-E) |
| 3 | `loan_status` | 8 | None | Status codes |
| 4 | `loan_officer` | 20 | None | Staff members |
| **Tier 2: Core Entity** | | | | |
| 5 | `customer` | 800 | industry | Business borrowers |
| **Tier 3: Business Process** | | | | |
| 6 | `application` | 3,000 | customer, loan_officer, loan_status | Loan applications |
| 7 | `loan` | 2,185 | application, customer, risk_grade, loan_status | Disbursed loans |
| **Tier 4: Transaction Details** | | | | |
| 8 | `repayment_schedule` | 78,996 | loan | Payment schedules |
| 9 | `payment` | 33,968 | loan | Actual payments |
| 10 | `default_event` | 232 | loan | Default records |

---

## Tier 1: Lookup Tables (No Dependencies)

These are standalone "enum" or "config" tables that don't depend on anything else. They form the foundation of the data model.

### 1. `industry` - Industry Classification

Defines what industry each business operates in, along with a historical baseline default rate.

| id | industry_code | industry_name | default_rate_baseline |
|----|---------------|---------------|----------------------|
| 1 | REST | Restaurant | 9.5 |
| 2 | RETAIL | Retail | 8.2 |
| 3 | TECH | Technology Services | 4.1 |
| 4 | CONST | Construction | 11.3 |
| 5 | HEALTH | Healthcare Services | 5.8 |

**Key Fields:**

- `default_rate_baseline` is the historical default rate, used for risk assessment and portfolio analysis
- Risk varies significantly by industry: Tech at 4.1% vs Construction at 11.3%

---

### 2. `risk_grade` - Risk Tiers

Defines 5 risk grades (A through E), each with its own credit score range, interest rate, and expected default rate.

| id | grade_code | grade_name | min_credit_score | max_credit_score | interest_rate | implied_default_rate |
|----|------------|------------|------------------|------------------|---------------|---------------------|
| 1 | A | Prime | 720 | 850 | 5.5% | 3.0% |
| 2 | B | Near Prime | 680 | 719 | 7.5% | 6.0% |
| 3 | C | Standard | 640 | 679 | 9.5% | 6.0% |
| 4 | D | Subprime | 600 | 639 | 12.5% | 13.0% |
| 5 | E | Deep Subprime | 300 | 599 | 16.0% | 18.0% |

**Business Insight:**

- `implied_default_rate` is the assumed default rate used for pricing
- Grade C is intentionally mispriced (implied 6%, but actual ~11.2%) to simulate a "risk pricing misalignment" scenario

---

### 3. `loan_status` - Status Codes

Status codes that span the entire loan lifecycle, grouped into three categories.

| id | status_code | status_name | status_category |
|----|-------------|-------------|-----------------|
| 1 | PENDING | Pending Review | Application |
| 2 | UNDER_REVIEW | Under Review | Application |
| 3 | APPROVED | Approved | Application |
| 4 | REJECTED | Rejected | Application |
| 5 | DISBURSED | Disbursed | Active |
| 6 | CURRENT | Current | Active |
| 7 | DEFAULTED | Defaulted | Closed |
| 8 | PAID_OFF | Paid Off | Closed |

**Category Logic:**

- `Application`: Under review
- `Active`: Loan is outstanding
- `Closed`: Loan has ended (either paid off or defaulted)

---

### 4. `loan_officer` - Staff Members

Employee info for staff who process loan applications.

| id | employee_id | first_name | last_name | hire_date | region |
|----|-------------|------------|-----------|-----------|--------|
| 1 | LO0001 | Danielle | Johnson | 2022-07-12 | Northern CA |
| 2 | LO0002 | Jeffrey | Doyle | 2024-07-14 | Northern CA |
| 3 | LO0003 | Patricia | Miller | 2023-04-06 | Bay Area |
| 4 | LO0004 | Anthony | Robinson | 2023-09-05 | Southern CA |
| 5 | LO0005 | Anthony | Gonzalez | 2024-05-26 | Southern CA |

**Business Use:**

- Used for analyzing each officer's approval efficiency, default rates, and other performance metrics
- `region` field enables regional performance analysis

---

## Tier 2: Core Entity Table

### 5. `customer` - Business Borrowers

Loan applicants—the small-to-medium businesses. This is the first table with a foreign key dependency.

| id | business_name | tax_id | industry_id | city | credit_score | is_repeat_customer |
|----|---------------|--------|-------------|------|--------------|-------------------|
| 1 | Watts, Robinson and Nguyen | 03-0564139 | 3 (TECH) | Sacramento | 553 | 0 |
| 2 | Lewis-Porter | 72-4238849 | 6 | Fresno | 722 | 0 |
| 3 | Ross, Robinson and Bright | 87-1012269 | 15 | Oakland | 685 | 0 |
| 4 | Carlson-Mcdonald | 48-0184514 | 1 (REST) | Sacramento | 700 | 0 |
| 5 | Smith-Bowen | 48-2814893 | 7 | San Jose | 698 | 0 |

**Key Fields:**

- `credit_score`: Business credit score (300-850), determines risk grade
- `is_repeat_customer`: Whether they've borrowed before (used for customer lifetime value analysis)
- `industry_id` → Foreign key to `industry` table

**Foreign Key:**

```
customer.industry_id → industry.id
```

---

## Tier 3: Business Process Tables

These tables capture the core lending workflow: from application to disbursement.

### 6. `application` - Loan Applications

Records details for each loan application. This is where the business process begins.

| id | application_number | customer_id | loan_officer_id | requested_amount | application_date | status_id | rejection_reason |
|----|-------------------|-------------|-----------------|------------------|------------------|-----------|------------------|
| 1 | APP-000001 | 412 | 6 | $323,000 | 2024-05-10 | 3 (APPROVED) | |
| 2 | APP-000002 | 454 | 18 | $216,000 | 2024-07-23 | 4 (REJECTED) | Industry risk concentration |
| 3 | APP-000003 | 783 | 11 | $361,000 | 2024-03-04 | 4 (REJECTED) | Collateral insufficient |
| 4 | APP-000004 | 559 | 18 | $431,000 | 2025-11-24 | 3 (APPROVED) | |
| 5 | APP-000005 | 369 | 13 | $50,000 | 2024-07-06 | 3 (APPROVED) | |

**Key Fields:**

- `rejection_reason`: Reason for rejection—useful for "approval leakage" analysis to find good customers who were incorrectly rejected
- About 73% of applications get approved, 27% get rejected

**Foreign Keys:**

```
application.customer_id → customer.id
application.loan_officer_id → loan_officer.id
application.status_id → loan_status.id
```

---

### 7. `loan` - Disbursed Loans

Only approved applications generate loan records. This has a **1:1 relationship** with `application`.

| id | loan_number | application_id | customer_id | risk_grade_id | approved_amount | interest_rate | term_months | current_status_id |
|----|-------------|----------------|-------------|---------------|-----------------|---------------|-------------|------------------|
| 1 | LN-000001 | 1 | 412 | 2 (Grade B) | $321,013 | 7.5% | 60 | 6 (CURRENT) |
| 2 | LN-000002 | 4 | 559 | 1 (Grade A) | $425,447 | 5.5% | 36 | 8 (PAID_OFF) |
| 3 | LN-000003 | 5 | 369 | 5 (Grade E) | $48,534 | 16.0% | 12 | 6 (CURRENT) |
| 4 | LN-000004 | 6 | 292 | 4 (Grade D) | $52,431 | 12.5% | 36 | 6 (CURRENT) |
| 5 | LN-000005 | 8 | 524 | 1 (Grade A) | $117,690 | 5.5% | 12 | 6 (CURRENT) |

**Key Fields:**

- `approved_amount`: Actual approved amount (may differ from requested)
- `interest_rate`: Annual rate based on risk grade
- `term_months`: Loan term (12/24/36/48/60 months)

**Foreign Keys (most complex table):**

```
loan.application_id → application.id (UNIQUE, 1:1)
loan.customer_id → customer.id
loan.risk_grade_id → risk_grade.id
loan.current_status_id → loan_status.id
```

---

## Tier 4: Transaction Detail Tables

These tables record post-disbursement transaction data, all dependent on the `loan` table.

### 8. `repayment_schedule` - Payment Schedule

Monthly payment schedule for each loan, broken down into principal and interest. **Highest record count** (78,996 rows).

| id | loan_id | installment_number | due_date | scheduled_payment | principal_portion | interest_portion | remaining_balance |
|----|---------|-------------------|----------|-------------------|-------------------|------------------|-------------------|
| 1 | 1 | 1 | 2024-07-08 | $6,432.44 | $4,426.11 | $2,006.33 | $316,586.94 |
| 2 | 1 | 2 | 2024-08-07 | $6,432.44 | $4,453.77 | $1,978.67 | $312,133.17 |
| 3 | 1 | 3 | 2024-09-06 | $6,432.44 | $4,481.61 | $1,950.83 | $307,651.56 |
| 4 | 1 | 4 | 2024-10-06 | $6,432.44 | $4,509.62 | $1,922.82 | $303,141.94 |
| 5 | 1 | 5 | 2024-11-05 | $6,432.44 | $4,537.80 | $1,894.64 | $298,604.14 |

**Key Fields:**

- `principal_portion` + `interest_portion` = `scheduled_payment`
- `remaining_balance`: Principal remaining after this payment
- Each loan generates 12-60 schedule records depending on term

**Foreign Key:**

```
repayment_schedule.loan_id → loan.id
```

---

### 9. `payment` - Actual Payments

Records actual payments received from borrowers, including days late. This is the core data source for "early warning" analysis.

| id | loan_id | payment_date | payment_amount | installment_number | days_late | payment_method |
|----|---------|--------------|----------------|-------------------|-----------|---------------|
| 1 | 1 | 2024-07-08 | $6,432.44 | 1 | 0 | Wire Transfer |
| 2 | 1 | 2024-08-15 | $4,163.11 | 2 | 8 | Check |
| 3 | 1 | 2024-09-16 | $6,432.44 | 3 | 10 | Credit Card |
| 4 | 1 | 2024-10-06 | $6,432.44 | 4 | 0 | Wire Transfer |
| 5 | 1 | 2024-11-05 | $6,432.44 | 5 | 0 | Wire Transfer |

**Key Fields:**

- `days_late`: Days past due (0 = on time)
- Notice installment #2: underpayment ($4,163 < $6,432) and 8 days late—this is an early warning sign

**Business Insight:**

- About 70% of payments are on time, 20% are 1-15 days late, 10% are 16-30 days late
- Late and partial payment patterns are key predictors of default

**Foreign Key:**

```
payment.loan_id → loan.id
```

---

### 10. `default_event` - Default Records

Records details for defaulted loans, including losses and warning signals. Has a **1:1 relationship** with `loan` (one loan can have at most one default event).

| id | loan_id | default_date | installments_missed | outstanding_at_default | recovery_amount | loss_amount | had_early_warning | warning_signals |
|----|---------|--------------|---------------------|------------------------|-----------------|-------------|-------------------|-----------------|
| 1 | 14 | 2025-09-07 | 54 | $107,544 | $51,387 | $56,157 | 0 | |
| 2 | 24 | 2025-10-03 | 7 | $90,597 | $25,863 | $64,734 | 1 | 1 late payments in last 3 months |
| 3 | 27 | 2026-01-29 | 8 | $234,780 | $103,963 | $130,817 | 1 | 1 late payments; 1 partial payments |
| 4 | 35 | 2026-06-28 | 14 | $63,877 | $13,600 | $50,277 | 1 | 2 late payments; 1 partial payments |
| 5 | 37 | 2026-09-12 | 15 | $104,201 | $40,455 | $63,746 | 0 | |

**Key Fields:**

- `had_early_warning`: Whether early warning signs were detected (about 72% of defaults had warnings)
- `warning_signals`: Description of warning signs
- `loss_amount` = `outstanding_at_default` - `recovery_amount`

**Foreign Key:**

```
default_event.loan_id → loan.id (UNIQUE, 1:1)
```

---

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐      ┌─────────────┐
│  industry   │     │ risk_grade  │     │ loan_status │      │loan_officer │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘      └──────┬──────┘
       │                   │                   │                    │
       │                   │         ┌─────────┼─────────┐          │
       ▼                   │         │         │         │          │
┌─────────────┐            │         │         │         │          │
│  customer   │────────────┼─────────┼─────────┤         │          │
└──────┬──────┘            │         │         │         │          │
       │                   │         │         │         │          │
       │    ┌──────────────┘         │         │         │          │
       │    │                        │         │         ▼          │
       ▼    ▼                        ▼         ▼    ┌─────────────┐ │
┌───────────────────────────────────────────────────│ application │◄┘
│                                                   └──────┬──────┘
│                                                          │
│                                                          ▼
│                                                 ┌─────────────┐
└────────────────────────────────────────────────►│    loan     │
                                                  └──────┬──────┘
                                                         │
                           ┌─────────────────────────────┼─────────────────────────────┐
                           │                             │                             │
                           ▼                             ▼                             ▼
                  ┌──────────────────┐           ┌─────────────┐           ┌──────────────────┐
                  │repayment_schedule│           │   payment   │           │  default_event   │
                  └──────────────────┘           └─────────────┘           └──────────────────┘
```

---

## Core Business Analysis Scenarios

This dataset is specifically designed for 5 key business analyses:

| # | Analysis | Key Tables | Business Question |
|---|----------|------------|-------------------|
| Q1 | Risk Pricing Alignment | risk_grade + loan + default_event | Are Grade C loans underpriced? |
| Q2 | Portfolio Concentration | industry + loan | Is restaurant exposure too high? |
| Q3 | Approval Leakage | application + customer | How many good customers are we wrongly rejecting? |
| Q4 | Early Warning Signals | payment + default_event | Can we predict defaults 3 months ahead? |
| Q5 | Customer Lifetime Value | customer + loan | Are repeat customers worth more than new ones? |

---

## Key Takeaways

1. **Tier 1** consists of 4 standalone "enum/config" tables that define business rules
2. **`customer`** is the core entity, linking to industry classification
3. **`application` → `loan`** is the critical conversion point (only APPROVED applications generate loans)
4. **`loan`** is the data hub, branching into three downstream tables:
   - `repayment_schedule`: What's owed
   - `payment`: What's been paid
   - `default_event`: What went wrong
5. By comparing `repayment_schedule` with `payment`, you can analyze payment behavior patterns

---

## Advanced Analytics Concepts

This section covers business metrics that are derived through multi-table JOINs or calculations. These concepts don't exist in any single table—they're computed from SQL queries.

### Concept Index

| Concept | Tables Involved | Business Use |
|---------|-----------------|--------------|
| Actual Default Rate | loan + default_event | Risk assessment |
| Pricing Gap | risk_grade + loan + default_event | Pricing calibration |
| Approval Rate | application + loan_status | Operational efficiency |
| False Rejection | application + customer | Revenue optimization |
| Late Payment Rate | payment | Risk monitoring |
| Partial Payment | payment + loan | Early warning |
| Recovery Rate | default_event | Loss estimation |
| Loss Severity | default_event | Reserve calculation |
| Expected Loss | loan + risk_grade | Risk exposure |
| Portfolio Concentration | loan + customer + industry | Diversification analysis |
| Days to Decision | application | SLA monitoring |
| Payment Behavior Cohort | payment + loan | Risk segmentation |
| Customer LTV | customer + loan + default_event | Customer tiering |
| Vintage Analysis | loan + default_event | Trend tracking |
| Risk Grade Migration | customer + loan + risk_grade | Refinancing opportunities |

---

### 1. Actual Default Rate

**Definition:** The percentage of disbursed loans that actually defaulted.

**Formula:** `defaulted_loans / total_loans × 100%`

**Tables & Fields:**
- `loan`: Count total loans
- `default_event`: Count defaults

**SQL Example:**

```sql
SELECT
    COUNT(de.id) AS defaults,
    COUNT(l.id) AS total_loans,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS actual_default_rate
FROM loan l
LEFT JOIN default_event de ON l.id = de.loan_id;
```

**Business Value:** Compare against `risk_grade.implied_default_rate` to see if pricing assumptions are accurate.

---

### 2. Pricing Gap

**Definition:** The difference between assumed default rate (used in pricing) and actual default rate.

**Formula:** `implied_default_rate - actual_default_rate`

**Tables & Fields:**
- `risk_grade.implied_default_rate`: Pricing assumption
- Calculated `actual_default_rate`: Actual performance

**SQL Example:**

```sql
SELECT
    rg.grade_code,
    rg.implied_default_rate AS pricing_assumption,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS actual_default_rate,
    ROUND(rg.implied_default_rate - 100.0 * COUNT(de.id) / COUNT(l.id), 2) AS pricing_gap
FROM risk_grade rg
JOIN loan l ON rg.id = l.risk_grade_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY rg.id, rg.grade_code, rg.implied_default_rate;
```

**Business Value:**
- **Positive gap:** Overpriced (charging too much), customers may leave
- **Negative gap:** Underpriced (not charging enough), company loses money
- Grade C has a pricing gap of about -5%, meaning significant underpricing

---

### 3. Approval Rate

**Definition:** The percentage of applications that get approved.

**Formula:** `approved_count / total_applications × 100%`

**Tables & Fields:**
- `application.status_id`
- `loan_status.status_code = 'APPROVED'`

**SQL Example:**

```sql
SELECT
    COUNT(*) AS total_applications,
    COUNT(CASE WHEN ls.status_code = 'APPROVED' THEN 1 END) AS approved,
    ROUND(100.0 * COUNT(CASE WHEN ls.status_code = 'APPROVED' THEN 1 END) / COUNT(*), 2) AS approval_rate
FROM application a
JOIN loan_status ls ON a.status_id = ls.id;
```

**Business Value:** Monitor underwriting strictness—too high leads to more defaults, too low loses revenue.

---

### 4. False Rejection / Approval Leakage

**Definition:** Applications that were rejected but actually fit the profile of successful borrowers.

**Criteria:** Rejected customers with credit_score, annual_revenue, and employee_count close to or above successful borrower averages.

**Tables & Fields:**
- `application` (status = REJECTED)
- `customer` (credit_score, annual_revenue, employee_count)
- Compare against successful borrower profiles

**SQL Example:**

```sql
-- First, calculate the average profile of successful borrowers
WITH successful_profile AS (
    SELECT
        AVG(c.credit_score) AS avg_score,
        AVG(c.annual_revenue) AS avg_revenue
    FROM loan l
    JOIN customer c ON l.customer_id = c.id
    JOIN loan_status ls ON l.current_status_id = ls.id
    WHERE ls.status_code IN ('CURRENT', 'PAID_OFF')  -- Performing loans
)
-- Find rejected applications with strong profiles
SELECT
    a.application_number,
    c.credit_score,
    a.rejection_reason
FROM application a
JOIN customer c ON a.customer_id = c.id
JOIN loan_status ls ON a.status_id = ls.id
CROSS JOIN successful_profile sp
WHERE ls.status_code = 'REJECTED'
  AND c.credit_score >= sp.avg_score - 30;  -- Credit score close to successful borrowers
```

**Business Value:** Each false rejection represents lost interest income—about 23% of rejections may be "false negatives."

---

### 5. Late Payment Rate

**Definition:** The percentage of payments that were late.

**Formula:** `late_payments / total_payments × 100%`

**Tables & Fields:**
- `payment.days_late` (> 0 means late)

**SQL Example:**

```sql
SELECT
    COUNT(*) AS total_payments,
    COUNT(CASE WHEN days_late > 0 THEN 1 END) AS late_payments,
    ROUND(100.0 * COUNT(CASE WHEN days_late > 0 THEN 1 END) / COUNT(*), 2) AS late_payment_rate,
    ROUND(AVG(CASE WHEN days_late > 0 THEN days_late END), 1) AS avg_days_late
FROM payment;
```

**Business Value:** Rising late payment rates are an early signal of portfolio deterioration, typically leading defaults by 6-12 months.

---

### 6. Partial Payment

**Definition:** Instances where the customer paid less than the scheduled amount.

**Criteria:** `payment_amount < monthly_payment × 95%` (5% tolerance)

**Tables & Fields:**
- `payment.payment_amount`
- `loan.monthly_payment`

**SQL Example:**

```sql
SELECT
    p.loan_id,
    p.installment_number,
    p.payment_amount AS actual_paid,
    l.monthly_payment AS scheduled,
    ROUND(100.0 * p.payment_amount / l.monthly_payment, 1) AS pct_paid
FROM payment p
JOIN loan l ON p.loan_id = l.id
WHERE p.payment_amount < l.monthly_payment * 0.95;
```

**Business Value:** Partial payments signal cash flow stress; combined with late payment patterns, they can predict defaults.

---

### 7. Recovery Rate

**Definition:** The percentage of defaulted exposure recovered through collections, asset sales, or legal proceedings.

**Formula:** `recovery_amount / outstanding_at_default × 100%`

**Tables & Fields:**
- `default_event.recovery_amount`
- `default_event.outstanding_at_default`

**SQL Example:**

```sql
SELECT
    SUM(recovery_amount) AS total_recovered,
    SUM(outstanding_at_default) AS total_exposure,
    ROUND(100.0 * SUM(recovery_amount) / SUM(outstanding_at_default), 2) AS recovery_rate
FROM default_event;
```

**Business Value:** Recovery rates affect reserve calculations—Grade A loans recover 40-50%, Grade E only 20-30%.

---

### 8. Loss Severity

**Definition:** Net loss as a percentage of defaulted exposure.

**Formula:** `loss_amount / outstanding_at_default × 100%` (or `1 - Recovery Rate`)

**Tables & Fields:**
- `default_event.loss_amount`
- `default_event.outstanding_at_default`

**SQL Example:**

```sql
SELECT
    rg.grade_code,
    ROUND(100.0 * SUM(de.loss_amount) / SUM(de.outstanding_at_default), 2) AS loss_severity
FROM default_event de
JOIN loan l ON de.loan_id = l.id
JOIN risk_grade rg ON l.risk_grade_id = rg.id
GROUP BY rg.grade_code;
```

**Business Value:** Used to calculate Expected Loss = Default Probability × Loss Severity × Exposure.

---

### 9. Expected Loss

**Definition:** Estimated potential loss based on risk grade.

**Formula:** `outstanding_balance × implied_default_rate / 100`

**Tables & Fields:**
- `loan.outstanding_balance`
- `risk_grade.implied_default_rate`

**SQL Example:**

```sql
SELECT
    l.loan_number,
    l.outstanding_balance,
    rg.implied_default_rate,
    ROUND(l.outstanding_balance * rg.implied_default_rate / 100, 2) AS expected_loss
FROM loan l
JOIN risk_grade rg ON l.risk_grade_id = rg.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE ls.status_code = 'CURRENT'
ORDER BY expected_loss DESC
LIMIT 10;
```

**Business Value:** Identify high-risk exposures and prioritize loans with the largest expected losses.

---

### 10. Portfolio Concentration

**Definition:** Percentage of the total portfolio held in a single industry.

**Formula:** `industry_exposure / total_exposure × 100%`

**Tables & Fields:**
- `loan.outstanding_balance`
- `customer.industry_id`
- `industry.industry_name`

**SQL Example:**

```sql
SELECT
    i.industry_name,
    SUM(l.outstanding_balance) AS industry_exposure,
    ROUND(100.0 * SUM(l.outstanding_balance) /
          (SELECT SUM(outstanding_balance) FROM loan), 2) AS pct_of_portfolio
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN industry i ON c.industry_id = i.id
GROUP BY i.industry_name
ORDER BY pct_of_portfolio DESC;
```

**Business Value:** Heavy concentration in any single industry creates systemic risk—restaurants are at ~28%, which may need a cap.

---

### 11. Days to Decision

**Definition:** Number of days from application submission to decision.

**Formula:** `decision_date - application_date`

**Tables & Fields:**
- `application.application_date`
- `application.decision_date`

**SQL Example:**

```sql
SELECT
    lo.first_name || ' ' || lo.last_name AS loan_officer,
    COUNT(a.id) AS applications_processed,
    ROUND(AVG(JULIANDAY(a.decision_date) - JULIANDAY(a.application_date)), 1) AS avg_days_to_decision,
    ROUND(100.0 * COUNT(CASE WHEN JULIANDAY(a.decision_date) - JULIANDAY(a.application_date) <= 7 THEN 1 END)
          / COUNT(a.id), 1) AS sla_compliance_pct
FROM application a
JOIN loan_officer lo ON a.loan_officer_id = lo.id
WHERE a.decision_date IS NOT NULL
GROUP BY lo.id;
```

**Business Value:** SLA target is typically 7 days—delays hurt customer experience and conversion rates.

---

### 12. Payment Behavior Cohort

**Definition:** Group loans by their first 6 months of payment behavior, then analyze default rates by cohort.

**Cohort Criteria:**
- Perfect: Never late, never partial
- Mostly On-Time: At most 1 late payment
- Problematic: 2+ late payments or any partial payments

**Tables & Fields:**
- `payment` (first 6 installments: days_late, payment_amount)
- `loan.monthly_payment`
- `default_event`

**SQL Example:**

```sql
WITH early_behavior AS (
    SELECT
        p.loan_id,
        SUM(CASE WHEN p.days_late > 0 THEN 1 ELSE 0 END) AS late_count,
        SUM(CASE WHEN p.payment_amount < l.monthly_payment * 0.95 THEN 1 ELSE 0 END) AS partial_count
    FROM payment p
    JOIN loan l ON p.loan_id = l.id
    WHERE p.installment_number <= 6
    GROUP BY p.loan_id
),
cohort AS (
    SELECT
        loan_id,
        CASE
            WHEN late_count = 0 AND partial_count = 0 THEN 'Perfect'
            WHEN late_count <= 1 AND partial_count = 0 THEN 'Mostly On-Time'
            ELSE 'Problematic'
        END AS cohort_name
    FROM early_behavior
)
SELECT
    c.cohort_name,
    COUNT(DISTINCT l.id) AS loan_count,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(DISTINCT l.id), 2) AS default_rate
FROM cohort c
JOIN loan l ON c.loan_id = l.id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY c.cohort_name;
```

**Business Value:** Problematic cohort has 15-25% default rates vs 2-4% for Perfect—use this for early intervention.

---

### 13. Customer Lifetime Value (LTV)

**Definition:** Total value a customer brings over their entire relationship.

**Formula:** `total_borrowed + estimated_interest - (defaults × avg_loss)`

**Tables & Fields:**
- `customer.is_repeat_customer`
- `loan.approved_amount`, `interest_rate`, `term_months`
- `default_event`

**SQL Example:**

```sql
SELECT
    CASE WHEN c.is_repeat_customer = 1 THEN 'Repeat' ELSE 'First-Time' END AS customer_type,
    COUNT(DISTINCT c.id) AS customer_count,
    COUNT(l.id) AS loan_count,
    ROUND(AVG(l.approved_amount), 0) AS avg_loan_amount,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS default_rate
FROM customer c
LEFT JOIN loan l ON c.id = l.customer_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY c.is_repeat_customer;
```

**Business Value:** Repeat customers default at ~3.2% vs ~9.1% for first-timers—invest in customer retention.

---

### 14. Vintage Analysis

**Definition:** Group loans by origination period (quarter/month) and track performance over time.

**Tables & Fields:**
- `loan.disbursement_date`
- `default_event`

**SQL Example:**

```sql
SELECT
    strftime('%Y-Q' || ((CAST(strftime('%m', l.disbursement_date) AS INTEGER) - 1) / 3 + 1),
             l.disbursement_date) AS quarter,
    COUNT(l.id) AS originations,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS default_rate
FROM loan l
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY quarter
ORDER BY quarter;
```

**Business Value:** If newer vintages show higher default rates than historical averages, underwriting standards may have loosened.

---

### 15. Risk Grade Migration

**Definition:** Customers whose credit scores have improved and may now qualify for better rates (migrate to a better risk grade).

**Criteria:** `current_credit_score > original_grade_max_credit_score`

**Tables & Fields:**
- `customer.credit_score`
- `loan.risk_grade_id`
- `risk_grade.max_credit_score`, `interest_rate`

**SQL Example:**

```sql
SELECT
    l.loan_number,
    c.credit_score AS current_score,
    rg_current.grade_code AS loan_grade,
    rg_current.max_credit_score AS grade_max,
    rg_current.interest_rate AS current_rate,
    l.outstanding_balance,
    -- Find the grade they now qualify for
    (SELECT rg2.grade_code FROM risk_grade rg2
     WHERE c.credit_score BETWEEN rg2.min_credit_score AND rg2.max_credit_score) AS qualified_grade
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN risk_grade rg_current ON l.risk_grade_id = rg_current.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE ls.status_code = 'CURRENT'
  AND c.credit_score > rg_current.max_credit_score + 10  -- Score now exceeds their grade
ORDER BY l.outstanding_balance DESC
LIMIT 10;
```

**Business Value:** Proactively reach out to offer refinancing—improves customer satisfaction and retention.

---

## How These Concepts Relate

```
                    ┌─────────────────┐
                    │  Risk Grade     │
                    │ implied_default │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌──────────┐ ┌──────────────┐
    │ Expected Loss   │ │ Pricing  │ │ Risk Grade   │
    │ = balance ×     │ │ Gap      │ │ Migration    │
    │   implied_rate  │ │          │ │              │
    └─────────────────┘ └────┬─────┘ └──────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │     Actual Default Rate      │
              │  = defaults / total_loans    │
              └──────────────┬───────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Recovery Rate   │ │ Loss Severity   │ │ Early Warning   │
│ = recovered /   │ │ = loss /        │ │ = late + partial│
│   exposure      │ │   exposure      │ │   payments      │
└─────────────────┘ └─────────────────┘ └────────┬────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │ Payment Behavior│
                                        │ Cohort          │
                                        └─────────────────┘
```

These concepts form the complete loan risk management framework:
1. **Pre-origination:** Expected Loss, Portfolio Concentration—control risk exposure
2. **During life of loan:** Late Payment Rate, Payment Behavior Cohort—monitor and intervene early
3. **Post-default:** Recovery Rate, Loss Severity—assess actual losses

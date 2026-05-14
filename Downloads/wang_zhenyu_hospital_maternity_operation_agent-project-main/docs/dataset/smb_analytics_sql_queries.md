# FinTech - SMB Lending Pipeline SQL Queries Reference

## Overview

This document provides **20 business-oriented SQL queries** designed for the `fintech_smb_lending_pipeline_medium` dataset. Each query addresses a real-world business question that stakeholders at Pacific Bridge Lending might ask when analyzing their lending operations, risk management, and portfolio performance.

---

## Query Index

| # | Title | Business Role | Category |
|---|-------|---------------|----------|
| 1 | Risk Grade Pricing Alignment Analysis | Executive | Aggregation + Join |
| 2 | Industry Portfolio Concentration Dashboard | Manager | Aggregation + Join |
| 3 | Approval Leakage - False Rejection Analysis | Analyst | Subquery + Join |
| 4 | Early Warning Signals Before Default | Analyst | Window Function + Join |
| 5 | Customer Lifecycle Value Comparison | Executive | Aggregation + Join |
| 6 | Monthly Application Volume Trends | Operations | Date Aggregation |
| 7 | Loan Officer Performance Scorecard | Manager | Aggregation + Join |
| 8 | Payment Behavior Cohort Analysis | Analyst | CTE + Aggregation |
| 9 | Top 10 Highest Risk Outstanding Loans | Operations | Join + Subquery |
| 10 | Default Recovery Rate by Risk Grade | Finance | Aggregation + Join |
| 11 | Customer Acquisition Cost by Region | Finance | Aggregation + Join |
| 12 | Repeat Customer Retention Metrics | Manager | CTE + Join |
| 13 | Portfolio Vintage Analysis | Analyst | Date + Aggregation |
| 14 | Late Payment Trend Analysis | Operations | Window Function |
| 15 | Loan Amount vs Credit Score Correlation | Analyst | Aggregation |
| 16 | Risk Grade Migration Opportunities | Manager | Subquery + Join |
| 17 | Monthly Cash Flow Projection | Finance | Aggregation + Date |
| 18 | Application Processing Time Analysis | Operations | Date Calculation |
| 19 | Industry-Specific Default Patterns | Executive | CTE + Aggregation |
| 20 | Customer Segmentation by LTV | Executive | CTE + Window Function |

---

## Queries

### Query 1: Risk Grade Pricing Alignment Analysis

**Business Context:**
The Chief Risk Officer needs to validate whether loan pricing (interest rates) accurately reflects actual default risk across all risk grades. During the quarterly risk review, she discovered that some risk grades may be mispriced—charging too little for the actual risk taken. This analysis compares the implied default rate used in pricing models against actual observed default rates. Discrepancies indicate either profit opportunities (charging too much) or losses (charging too little). This is the foundation for Q1 in the consulting project and directly impacts profitability targets.

**Category:** Aggregation + Join
**Difficulty:** Intermediate
**Business Role:** Executive

```sql
-- Compare implied vs actual default rates by risk grade to identify pricing misalignment
SELECT
    rg.grade_code,
    rg.grade_name,
    rg.interest_rate,
    rg.implied_default_rate AS pricing_assumption_pct,
    COUNT(l.id) AS total_loans,
    COUNT(de.id) AS defaulted_loans,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS actual_default_rate_pct,
    ROUND(rg.implied_default_rate - (100.0 * COUNT(de.id) / COUNT(l.id)), 2) AS pricing_gap_pct
FROM risk_grade rg
JOIN loan l ON rg.id = l.risk_grade_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY rg.id, rg.grade_code, rg.grade_name, rg.interest_rate, rg.implied_default_rate
ORDER BY pricing_gap_pct ASC;
```

**Expected Result Description:**
Returns one row per risk grade showing total loans, default counts, actual vs implied default rates, and the pricing gap. Negative pricing gaps indicate underpricing (actual defaults exceed assumptions), while positive gaps indicate overpricing. Grade C is expected to show a significant negative gap (~-5.2%), meaning Pacific Bridge loses money on these loans. Grade A may show customers withdrawing due to rates being too high relative to risk. This analysis quantifies the $1.1M-$2.0M annual loss mentioned in the consulting project.

---

### Query 2: Industry Portfolio Concentration Dashboard

**Business Context:**
The Portfolio Manager is preparing for a quarterly board meeting where she must report on portfolio diversification and concentration risk. The board is concerned about exposure to cyclical industries like hospitality and restaurants, especially after the pandemic. If any single industry experiences a systemic shock, the concentrated exposure could lead to cascading defaults. This query identifies which industries dominate the outstanding loan portfolio and calculates the concentration risk metrics that inform the company's appetite for new applications in overrepresented sectors.

**Category:** Aggregation + Join
**Difficulty:** Intermediate
**Business Role:** Manager

```sql
-- Calculate portfolio concentration by industry with exposure and default metrics
SELECT
    i.industry_name,
    COUNT(DISTINCT a.id) AS total_applications,
    ROUND(100.0 * COUNT(DISTINCT a.id) / (SELECT COUNT(*) FROM application), 2) AS pct_of_applications,
    COUNT(DISTINCT l.id) AS total_loans,
    ROUND(SUM(l.outstanding_balance), 2) AS total_outstanding,
    ROUND(100.0 * SUM(l.outstanding_balance) / (SELECT SUM(outstanding_balance) FROM loan), 2) AS pct_of_portfolio,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(DISTINCT l.id), 2) AS industry_default_rate_pct,
    i.default_rate_baseline AS historical_baseline_pct
FROM industry i
JOIN customer c ON i.id = c.industry_id
JOIN application a ON c.id = a.customer_id
LEFT JOIN loan l ON a.id = l.application_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY i.id, i.industry_name, i.default_rate_baseline
ORDER BY total_outstanding DESC;
```

**Expected Result Description:**
Returns industry-level metrics showing application volume, loan counts, outstanding balances, and default rates. Restaurants are expected to show ~18% of applications but ~28% of outstanding balance, revealing concentration risk. The query also compares current default rates against historical baselines to identify industries performing worse than expected. This supports Q2 (portfolio concentration) and helps justify sector-specific lending caps or pricing adjustments.

---

### Query 3: Approval Leakage - False Rejection Analysis

**Business Context:**
The VP of Lending is concerned about revenue lost from rejecting creditworthy applicants (false negatives). During a review of rejected applications, the team noticed some rejections had credit profiles similar to or better than approved loans that performed well. Each false rejection represents lost interest income, and at scale, this could mean hundreds of thousands in annual revenue. This analysis identifies rejected applications that look like "good customers" based on credit score, revenue, and employee count thresholds, helping quantify the opportunity cost of overly conservative underwriting.

**Category:** Subquery + Join
**Difficulty:** Advanced
**Business Role:** Analyst

```sql
-- Identify rejected applications with customer profiles matching successful borrowers
WITH successful_profile AS (
    SELECT
        AVG(c.credit_score) AS avg_credit_score,
        AVG(c.annual_revenue) AS avg_revenue,
        AVG(c.employee_count) AS avg_employees
    FROM loan l
    JOIN customer c ON l.customer_id = c.id
    JOIN loan_status ls ON l.current_status_id = ls.id
    WHERE ls.status_code IN ('CURRENT', 'PAID_OFF')
)
SELECT
    a.application_number,
    c.business_name,
    c.credit_score,
    c.annual_revenue,
    c.employee_count,
    a.requested_amount,
    a.rejection_reason,
    ROUND(c.credit_score - sp.avg_credit_score, 0) AS credit_score_vs_avg,
    ROUND(c.annual_revenue - sp.avg_revenue, 0) AS revenue_vs_avg
FROM application a
JOIN customer c ON a.customer_id = c.id
JOIN loan_status ls ON a.status_id = ls.id
CROSS JOIN successful_profile sp
WHERE ls.status_code = 'REJECTED'
  AND c.credit_score >= sp.avg_credit_score - 30
  AND c.annual_revenue >= sp.avg_revenue * 0.7
  AND c.employee_count >= sp.avg_employees * 0.6
ORDER BY c.credit_score DESC
LIMIT 50;
```

**Expected Result Description:**
Returns up to 50 rejected applications where the customer's profile (credit score, revenue, employees) matches or exceeds successful borrowers. Each row represents a potential false rejection. The analysis shows how close these rejected customers are to the "successful borrower" benchmark. Expected to find ~23% of rejections (170 per year) meeting this criteria, representing ~$850K in lost annual interest income. This directly supports Q3 (approval leakage) and provides specific applications for manual review and model recalibration.

---

### Query 4: Early Warning Signals Before Default

**Business Context:**
The Collections Manager wants to implement a proactive outreach program to prevent defaults before they happen. Historically, the company has only acted after loans became 90+ days past due, by which point recovery is difficult. This analysis examines payment behavior in the months leading up to defaults to identify early warning patterns like increasing lateness or partial payments. If the team can detect deterioration 3+ months early, they can intervene with restructuring offers, saving losses and customer relationships.

**Category:** Window Function + Join
**Difficulty:** Advanced
**Business Role:** Analyst

```sql
-- Analyze payment behavior patterns in the 3 months before defaults
WITH default_loan_payments AS (
    SELECT
        de.loan_id,
        de.default_date,
        p.payment_date,
        p.installment_number,
        p.days_late,
        p.payment_amount,
        l.monthly_payment,
        ROUND(100.0 * p.payment_amount / l.monthly_payment, 2) AS pct_of_scheduled,
        JULIANDAY(de.default_date) - JULIANDAY(p.payment_date) AS days_before_default
    FROM default_event de
    JOIN loan l ON de.loan_id = l.id
    JOIN payment p ON l.id = p.loan_id
    WHERE JULIANDAY(de.default_date) - JULIANDAY(p.payment_date) BETWEEN 0 AND 90
)
SELECT
    loan_id,
    default_date,
    COUNT(*) AS payments_in_90_days_prior,
    AVG(days_late) AS avg_days_late,
    MAX(days_late) AS max_days_late,
    AVG(pct_of_scheduled) AS avg_pct_paid,
    COUNT(CASE WHEN days_late > 10 THEN 1 END) AS late_payment_count,
    COUNT(CASE WHEN pct_of_scheduled < 95 THEN 1 END) AS partial_payment_count
FROM default_loan_payments
GROUP BY loan_id, default_date
HAVING payments_in_90_days_prior >= 2
ORDER BY max_days_late DESC, avg_pct_paid ASC
LIMIT 20;
```

**Expected Result Description:**
Returns defaulted loans with aggregated payment behavior metrics from the 90 days before default. Shows average lateness, maximum lateness, payment completion percentage, and counts of problematic payments. Expected to find that 72% of defaults showed deteriorating behavior (late payments, partial payments) in this window. Loans with avg_days_late > 10 or avg_pct_paid < 90% are strong candidates for early intervention. This supports Q4 (early warning signals) and justifies building a predictive monitoring dashboard.

---

### Query 5: Customer Lifecycle Value Comparison

**Business Context:**
The CEO is reviewing the customer acquisition strategy and budget allocation. The marketing team wants to invest heavily in new customer acquisition through digital ads, but the CFO argues that nurturing existing customers for repeat business may be more profitable. This analysis compares repeat customers (those who have taken multiple loans) against first-time borrowers across key metrics: default rates, average loan amounts, and approval rates. Understanding the lifetime value difference helps the executive team decide how to allocate the $2M annual marketing budget.

**Category:** Aggregation + Join
**Difficulty:** Intermediate
**Business Role:** Executive

```sql
-- Compare performance metrics between repeat and first-time customers
SELECT
    c.is_repeat_customer,
    CASE WHEN c.is_repeat_customer = 1 THEN 'Repeat Customer' ELSE 'First-Time Customer' END AS customer_type,
    COUNT(DISTINCT c.id) AS total_customers,
    COUNT(DISTINCT a.id) AS total_applications,
    COUNT(DISTINCT l.id) AS total_loans,
    ROUND(100.0 * COUNT(DISTINCT l.id) / COUNT(DISTINCT a.id), 2) AS approval_rate_pct,
    ROUND(AVG(l.approved_amount), 2) AS avg_loan_amount,
    ROUND(SUM(l.outstanding_balance), 2) AS total_outstanding,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(DISTINCT l.id), 2) AS default_rate_pct,
    ROUND(AVG(c.credit_score), 0) AS avg_credit_score
FROM customer c
LEFT JOIN application a ON c.id = a.customer_id
LEFT JOIN loan l ON a.id = l.application_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY c.is_repeat_customer
ORDER BY c.is_repeat_customer DESC;
```

**Expected Result Description:**
Returns two rows comparing repeat vs first-time customers across all key metrics. Repeat customers are expected to show significantly better performance: 3.2% default rate vs 9.1% for first-timers, 40-60% higher average loan amounts, and 5-10 points higher average credit scores. Despite being only 15% of the customer base, repeat customers drive disproportionate value. This supports Q5 (customer lifecycle value) and justifies reallocating marketing budget from acquisition to retention programs.

---

### Query 6: Monthly Application Volume Trends

**Business Context:**
The Operations Director needs to plan staffing levels for the underwriting team. Application volumes fluctuate seasonally, and understaffing during peak months leads to slow decision times (hurting customer experience), while overstaffing in slow months wastes payroll budget. This query analyzes monthly application volumes and approval rates over the past 2 years to identify patterns. The insights help the director schedule vacations during slow periods, bring on temporary contractors during peaks, and set realistic SLA targets for application processing times.

**Category:** Date Aggregation
**Difficulty:** Basic
**Business Role:** Operations

```sql
-- Track monthly application volume and approval rates over time
SELECT
    strftime('%Y-%m', a.application_date) AS month,
    COUNT(*) AS total_applications,
    COUNT(CASE WHEN ls.status_code = 'APPROVED' THEN 1 END) AS approved,
    COUNT(CASE WHEN ls.status_code = 'REJECTED' THEN 1 END) AS rejected,
    ROUND(100.0 * COUNT(CASE WHEN ls.status_code = 'APPROVED' THEN 1 END) / COUNT(*), 2) AS approval_rate_pct,
    ROUND(SUM(a.requested_amount), 2) AS total_requested_amount
FROM application a
JOIN loan_status ls ON a.status_id = ls.id
WHERE a.application_date IS NOT NULL
GROUP BY strftime('%Y-%m', a.application_date)
ORDER BY month ASC;
```

**Expected Result Description:**
Returns monthly time series data showing application counts, approvals, rejections, approval rates, and total requested amounts. Reveals seasonal patterns (e.g., Q1 slow, Q4 high volumes) and any sudden changes in approval rates that might indicate policy changes or economic shifts. The operations team uses this to forecast staffing needs 3-6 months ahead and to benchmark current performance against historical norms.

---

### Query 7: Loan Officer Performance Scorecard

**Business Context:**
The Head of Underwriting conducts quarterly performance reviews for all loan officers. She needs objective metrics to evaluate each officer's portfolio quality, productivity, and risk management. High-performing officers should be rewarded and given more complex applications, while underperformers may need additional training or coaching. This scorecard tracks applications processed, approval rates, average loan sizes, and default rates by officer. Officers with high approval rates but also high defaults may be approving too liberally, while those with very low approval rates may be overly conservative.

**Category:** Aggregation + Join
**Difficulty:** Intermediate
**Business Role:** Manager

```sql
-- Generate performance scorecard for each loan officer
SELECT
    lo.employee_id,
    lo.first_name || ' ' || lo.last_name AS officer_name,
    lo.region,
    COUNT(a.id) AS applications_processed,
    COUNT(l.id) AS loans_approved,
    ROUND(100.0 * COUNT(l.id) / COUNT(a.id), 2) AS approval_rate_pct,
    ROUND(AVG(l.approved_amount), 2) AS avg_loan_size,
    ROUND(SUM(l.outstanding_balance), 2) AS total_portfolio_balance,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / NULLIF(COUNT(l.id), 0), 2) AS default_rate_pct
FROM loan_officer lo
JOIN application a ON lo.id = a.loan_officer_id
LEFT JOIN loan l ON a.id = l.application_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY lo.id, lo.employee_id, lo.first_name, lo.last_name, lo.region
HAVING applications_processed >= 10
ORDER BY applications_processed DESC;
```

**Expected Result Description:**
Returns one row per loan officer showing productivity (applications processed), risk appetite (approval rate), portfolio size, and credit quality (default rate). The manager looks for balanced profiles: officers with 70-75% approval rates and <10% default rates are performing well. Outliers in either direction warrant discussion. This data drives compensation decisions, territory assignments, and training priorities.

---

### Query 8: Payment Behavior Cohort Analysis

**Business Context:**
The Analytics team is building a predictive model to identify loans at risk of default. One hypothesis is that payment behavior patterns (on-time vs late vs partial) in the first 6 months strongly predict long-term outcomes. This cohort analysis groups loans by their early payment behavior and tracks default rates for each cohort. If the data shows that loans with even one late payment in months 1-6 have 3x higher default rates, the team can trigger proactive interventions immediately rather than waiting for multiple missed payments.

**Category:** CTE + Aggregation
**Difficulty:** Advanced
**Business Role:** Analyst

```sql
-- Analyze default rates by early payment behavior cohorts
WITH early_payment_behavior AS (
    SELECT
        p.loan_id,
        COUNT(*) AS payments_made,
        SUM(CASE WHEN p.days_late = 0 THEN 1 ELSE 0 END) AS on_time_count,
        SUM(CASE WHEN p.days_late > 0 THEN 1 ELSE 0 END) AS late_count,
        AVG(CASE WHEN p.days_late > 0 THEN p.days_late END) AS avg_late_days,
        SUM(CASE WHEN p.payment_amount < l.monthly_payment * 0.95 THEN 1 ELSE 0 END) AS partial_count
    FROM payment p
    JOIN loan l ON p.loan_id = l.id
    WHERE p.installment_number <= 6
    GROUP BY p.loan_id
    HAVING COUNT(*) >= 3
),
cohort_classification AS (
    SELECT
        loan_id,
        CASE
            WHEN late_count = 0 AND partial_count = 0 THEN 'Perfect'
            WHEN late_count <= 1 AND partial_count = 0 THEN 'Mostly On-Time'
            WHEN late_count >= 2 OR partial_count >= 1 THEN 'Problematic'
            ELSE 'Other'
        END AS cohort
    FROM early_payment_behavior
)
SELECT
    cc.cohort,
    COUNT(DISTINCT l.id) AS total_loans,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(DISTINCT l.id), 2) AS default_rate_pct,
    ROUND(AVG(l.approved_amount), 2) AS avg_loan_amount
FROM cohort_classification cc
JOIN loan l ON cc.loan_id = l.id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY cc.cohort
ORDER BY default_rate_pct DESC;
```

**Expected Result Description:**
Returns default rates for three payment behavior cohorts: Perfect (all on-time), Mostly On-Time (1 late payment max), and Problematic (2+ late or partial payments). Expected to show that Problematic loans have 15-25% default rates vs 2-4% for Perfect payers. This validates the early warning hypothesis and provides thresholds for triggering automated alerts in the monitoring system.

---

### Query 9: Top 10 Highest Risk Outstanding Loans

**Business Context:**
During the weekly risk committee meeting, the Chief Credit Officer needs to review the current portfolio's highest-risk exposures. These are large loans that are either already showing signs of distress (late payments) or have high risk grades with substantial outstanding balances. The committee discusses whether to increase reserves, reach out to borrowers, or consider loan sales to reduce concentration. This query identifies the top 10 loans by risk-adjusted exposure (balance × risk score) that warrant immediate attention.

**Category:** Join + Subquery
**Difficulty:** Intermediate
**Business Role:** Operations

```sql
-- Identify the highest risk outstanding loans requiring immediate attention
SELECT
    l.loan_number,
    c.business_name,
    i.industry_name,
    rg.grade_code AS risk_grade,
    l.outstanding_balance,
    l.disbursement_date,
    ROUND((JULIANDAY('now') - JULIANDAY(l.disbursement_date)) / 30, 0) AS months_since_disbursement,
    (SELECT AVG(p2.days_late)
     FROM payment p2
     WHERE p2.loan_id = l.id AND p2.installment_number >=
           (SELECT MAX(p3.installment_number) - 2 FROM payment p3 WHERE p3.loan_id = l.id)
    ) AS avg_days_late_last_3,
    ls.status_name,
    ROUND(l.outstanding_balance * rg.implied_default_rate / 100, 2) AS expected_loss_amount
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN industry i ON c.industry_id = i.id
JOIN risk_grade rg ON l.risk_grade_id = rg.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE ls.status_code = 'CURRENT'
  AND l.outstanding_balance > 50000
ORDER BY expected_loss_amount DESC, avg_days_late_last_3 DESC
LIMIT 10;
```

**Expected Result Description:**
Returns the 10 loans with the highest expected loss exposure, calculated as outstanding_balance × implied_default_rate. Includes recent payment behavior (last 3 payments average lateness) to flag loans showing early warning signals. Each loan listed represents a concentration risk that may require loss reserves, credit monitoring, or proactive outreach. The committee uses this to prioritize collection efforts and update risk reports for investors.

---

### Query 10: Default Recovery Rate by Risk Grade

**Business Context:**
The CFO is preparing financial statements and needs to estimate loss reserves for the current loan portfolio. Loss reserves depend on both default probability (which varies by risk grade) and loss severity (how much is recovered after default). This query calculates recovery rates by risk grade, showing what percentage of defaulted balances were ultimately recovered through collections, asset sales, or legal proceedings. Lower recovery rates mean higher required reserves, impacting the company's capital requirements and profitability.

**Category:** Aggregation + Join
**Difficulty:** Intermediate
**Business Role:** Finance

```sql
-- Calculate recovery rates on defaulted loans by risk grade
SELECT
    rg.grade_code,
    rg.grade_name,
    COUNT(de.id) AS total_defaults,
    ROUND(SUM(de.outstanding_at_default), 2) AS total_exposure_at_default,
    ROUND(SUM(de.recovery_amount), 2) AS total_recovered,
    ROUND(SUM(de.loss_amount), 2) AS total_net_loss,
    ROUND(100.0 * SUM(de.recovery_amount) / SUM(de.outstanding_at_default), 2) AS recovery_rate_pct,
    ROUND(100.0 * SUM(de.loss_amount) / SUM(de.outstanding_at_default), 2) AS loss_severity_pct,
    ROUND(AVG(de.recovery_amount), 2) AS avg_recovery_per_default,
    ROUND(AVG(de.loss_amount), 2) AS avg_loss_per_default
FROM default_event de
JOIN loan l ON de.loan_id = l.id
JOIN risk_grade rg ON l.risk_grade_id = rg.id
GROUP BY rg.id, rg.grade_code, rg.grade_name
ORDER BY rg.id;
```

**Expected Result Description:**
Returns recovery metrics for each risk grade showing total defaults, exposure amounts, recoveries, net losses, recovery rates, and loss severity. Expected recovery rates range from 40-50% for Grade A loans (good collateral, cooperative borrowers) down to 20-30% for Grade E (limited assets, adversarial). The CFO multiplies default_rate × loss_severity to calculate expected loss provisions. Lower-than-expected recovery rates may indicate weaknesses in the collections process or collateral documentation.

---

### Query 11: Customer Acquisition Cost by Region

**Business Context:**
The Marketing Director is analyzing the efficiency of regional marketing campaigns. Pacific Bridge spends money on digital ads, events, and partnerships in four California regions: Northern CA, Southern CA, Bay Area, and Central Valley. This analysis divides total application volume by region to understand which areas generate the most applications and ultimately the most profitable loans. If Bay Area generates 40% of applications but only 20% come from paid marketing (rest are referrals), that changes how to allocate the ad budget across regions.

**Category:** Aggregation + Join
**Difficulty:** Basic
**Business Role:** Finance

```sql
-- Analyze application and loan volume by loan officer region (proxy for customer region)
SELECT
    lo.region,
    COUNT(DISTINCT a.id) AS total_applications,
    COUNT(DISTINCT l.id) AS approved_loans,
    ROUND(100.0 * COUNT(DISTINCT l.id) / COUNT(DISTINCT a.id), 2) AS conversion_rate_pct,
    ROUND(AVG(l.approved_amount), 2) AS avg_loan_size,
    ROUND(SUM(l.approved_amount), 2) AS total_loan_volume,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / NULLIF(COUNT(DISTINCT l.id), 0), 2) AS default_rate_pct
FROM loan_officer lo
JOIN application a ON lo.id = a.loan_officer_id
LEFT JOIN loan l ON a.id = l.application_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY lo.region
ORDER BY total_loan_volume DESC;
```

**Expected Result Description:**
Returns metrics by region showing application volume, conversion rates (approval %), average loan sizes, total volume, and default rates. Regions with high volume but low conversion may indicate loose lead quality or too-strict underwriting. Regions with high defaults may need risk-adjusted pricing. The marketing team uses cost-per-application data (from external systems) divided by this volume to calculate true customer acquisition costs, guiding budget allocation decisions.

---

### Query 12: Repeat Customer Retention Metrics

**Business Context:**
The Customer Success team wants to implement a formal retention program targeting customers approaching loan maturity. If the company can convert 30% of maturing loans into renewals or new loans, it could double the repeat customer base from 15% to 30%, significantly improving profitability (repeat customers default at 3.2% vs 9.1% for new customers). This query identifies customers who had a loan mature or paid off in the last 6 months but have not returned with a new application, representing the retention opportunity pool.

**Category:** CTE + Join
**Difficulty:** Advanced
**Business Role:** Manager

```sql
-- Identify customers who completed a loan but haven't returned for repeat business
WITH completed_loans AS (
    SELECT
        c.id AS customer_id,
        c.business_name,
        c.industry_id,
        MAX(l.maturity_date) AS last_maturity_date,
        COUNT(l.id) AS total_loans_taken
    FROM customer c
    JOIN loan l ON c.id = l.customer_id
    JOIN loan_status ls ON l.current_status_id = ls.id
    WHERE ls.status_code = 'PAID_OFF'
    GROUP BY c.id, c.business_name, c.industry_id
),
recent_applications AS (
    SELECT DISTINCT customer_id
    FROM application
    WHERE application_date >= DATE('now', '-6 months')
)
SELECT
    cl.customer_id,
    cl.business_name,
    i.industry_name,
    cl.last_maturity_date,
    ROUND((JULIANDAY('now') - JULIANDAY(cl.last_maturity_date)) / 30, 0) AS months_since_completion,
    cl.total_loans_taken,
    CASE WHEN ra.customer_id IS NOT NULL THEN 'Re-engaged' ELSE 'Dormant' END AS status
FROM completed_loans cl
JOIN industry i ON cl.industry_id = i.id
LEFT JOIN recent_applications ra ON cl.customer_id = ra.customer_id
WHERE cl.last_maturity_date >= DATE('now', '-12 months')
ORDER BY cl.last_maturity_date ASC;
```

**Expected Result Description:**
Returns customers who successfully paid off a loan in the last 12 months, flagging whether they've applied again recently. "Dormant" customers are the retention opportunity pool—they've proven to be good borrowers (paid off loans) but aren't being re-engaged. The Customer Success team reaches out to dormant customers with personalized offers (higher limits, better rates) to drive repeat business. Converting 100 dormant customers could generate $15-20M in new loan volume.

---

### Query 13: Portfolio Vintage Analysis

**Business Context:**
The Investment Committee reviews loan performance by origination cohort (vintage) to understand how credit quality and pricing have evolved over time. Loans originated in different periods may perform differently due to economic conditions, underwriting policy changes, or risk appetite shifts. This vintage analysis groups loans by origination quarter and tracks default rates, showing whether recent underwriting is tighter or looser than historical norms. Deteriorating vintage performance is an early warning of systemic credit quality issues.

**Category:** Date + Aggregation
**Difficulty:** Intermediate
**Business Role:** Analyst

```sql
-- Analyze loan performance by origination vintage (quarter)
SELECT
    strftime('%Y-Q', l.disbursement_date, 'start of month',
             CASE CAST(strftime('%m', l.disbursement_date) AS INTEGER)
                 WHEN 1 THEN 0 WHEN 2 THEN 0 WHEN 3 THEN 0
                 WHEN 4 THEN -3 WHEN 5 THEN -3 WHEN 6 THEN -3
                 WHEN 7 THEN -6 WHEN 8 THEN -6 WHEN 9 THEN -6
                 WHEN 10 THEN -9 WHEN 11 THEN -9 WHEN 12 THEN -9
             END || ' month') AS origination_quarter,
    COUNT(l.id) AS loans_originated,
    ROUND(SUM(l.approved_amount), 2) AS total_volume,
    ROUND(AVG(l.approved_amount), 2) AS avg_loan_size,
    ROUND(AVG(l.interest_rate), 2) AS avg_interest_rate,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS default_rate_pct,
    ROUND(SUM(CASE WHEN ls.status_code = 'PAID_OFF' THEN 1 ELSE 0 END) * 100.0 / COUNT(l.id), 2) AS payoff_rate_pct
FROM loan l
JOIN loan_status ls ON l.current_status_id = ls.id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY origination_quarter
ORDER BY origination_quarter DESC;
```

**Expected Result Description:**
Returns quarterly cohorts showing origination volume, average loan characteristics, default rates, and payoff rates. Recent quarters have limited seasoning (maturity), so default rates appear low—but the trend matters more than absolute levels. If 2024-Q1 shows 12% defaults while 2023-Q1 showed 8% at the same age, that indicates deteriorating credit quality. The committee uses this to assess whether current underwriting standards are adequate or need tightening.

---

### Query 14: Late Payment Trend Analysis

**Business Context:**
The Collections Manager tracks late payment rates month-over-month to detect emerging portfolio stress before it becomes defaults. An uptick in late payments (even 5-15 days late) often precedes defaults by 6-12 months, giving the team time to intervene. This trend analysis shows what percentage of payments each month are late, how late they are on average, and whether the situation is improving or deteriorating. A rising late payment rate may indicate economic headwinds affecting borrowers, requiring tighter underwriting or increased collection efforts.

**Category:** Window Function
**Difficulty:** Intermediate
**Business Role:** Operations

```sql
-- Track late payment rates and severity trends by month
SELECT
    strftime('%Y-%m', p.payment_date) AS payment_month,
    COUNT(*) AS total_payments,
    COUNT(CASE WHEN p.days_late = 0 THEN 1 END) AS on_time,
    COUNT(CASE WHEN p.days_late BETWEEN 1 AND 15 THEN 1 END) AS late_1_15_days,
    COUNT(CASE WHEN p.days_late BETWEEN 16 AND 30 THEN 1 END) AS late_16_30_days,
    ROUND(100.0 * COUNT(CASE WHEN p.days_late > 0 THEN 1 END) / COUNT(*), 2) AS late_payment_rate_pct,
    ROUND(AVG(CASE WHEN p.days_late > 0 THEN p.days_late END), 2) AS avg_days_late_when_late,
    ROUND(100.0 * SUM(CASE WHEN p.payment_amount < l.monthly_payment * 0.95 THEN 1 ELSE 0 END) / COUNT(*), 2) AS partial_payment_rate_pct
FROM payment p
JOIN loan l ON p.loan_id = l.id
WHERE p.payment_date >= DATE('now', '-12 months')
GROUP BY payment_month
ORDER BY payment_month ASC;
```

**Expected Result Description:**
Returns monthly time series showing payment counts broken down by lateness buckets and partial payment rates. The collections team looks for trends: if late_payment_rate increases from 25% to 35% over 3 months, that signals portfolio stress requiring action. Conversely, declining lateness indicates improving portfolio health. This data feeds into monthly executive dashboards and determines staffing levels for the collections team.

---

### Query 15: Loan Amount vs Credit Score Correlation

**Business Context:**
The Underwriting team is reviewing loan sizing guidelines. Current policy allows loan amounts up to 2x annual revenue, but the team suspects that large loans to lower-credit-score borrowers perform poorly. This analysis examines the relationship between approved loan amounts, customer credit scores, and default outcomes. If the data shows that loans >$300K to borrowers with <680 credit scores have 20%+ default rates, the policy should add credit score requirements to the loan sizing formula, not just revenue-based limits.

**Category:** Aggregation
**Difficulty:** Basic
**Business Role:** Analyst

```sql
-- Analyze relationship between loan amounts, credit scores, and default rates
SELECT
    CASE
        WHEN c.credit_score < 640 THEN 'Below 640'
        WHEN c.credit_score BETWEEN 640 AND 679 THEN '640-679'
        WHEN c.credit_score BETWEEN 680 AND 719 THEN '680-719'
        WHEN c.credit_score >= 720 THEN '720+'
    END AS credit_score_bucket,
    CASE
        WHEN l.approved_amount < 100000 THEN 'Under $100K'
        WHEN l.approved_amount BETWEEN 100000 AND 199999 THEN '$100K-$199K'
        WHEN l.approved_amount BETWEEN 200000 AND 299999 THEN '$200K-$299K'
        WHEN l.approved_amount >= 300000 THEN '$300K+'
    END AS loan_size_bucket,
    COUNT(l.id) AS loan_count,
    ROUND(AVG(l.approved_amount), 2) AS avg_loan_amount,
    COUNT(de.id) AS defaults,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS default_rate_pct
FROM loan l
JOIN customer c ON l.customer_id = c.id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY credit_score_bucket, loan_size_bucket
ORDER BY credit_score_bucket, loan_size_bucket;
```

**Expected Result Description:**
Returns a cross-tabulation showing default rates for each combination of credit score range and loan size bucket. Expected to reveal that large loans ($300K+) to lower credit scores (<680) have disproportionately high default rates (15-20%), while large loans to high credit scores (720+) perform well (3-5%). This justifies implementing tiered loan size limits based on credit score, e.g., <640 max $150K, 640-719 max $250K, 720+ max $500K.

---

### Query 16: Risk Grade Migration Opportunities

**Business Context:**
The Relationship Manager wants to identify customers who have improved their creditworthiness since their loan was originated. These customers may qualify for refinancing at better rates (lower risk grades), generating goodwill and preventing them from refinancing with competitors. A customer who took a loan at Grade C (9.5% rate) two years ago but now qualifies for Grade B (7.5%) could save $3,600/year on a $200K loan. Proactive outreach to offer refinancing improves customer satisfaction and retention.

**Category:** Subquery + Join
**Difficulty:** Advanced
**Business Role:** Manager

```sql
-- Identify borrowers whose current credit profile qualifies for better risk grade
SELECT
    l.loan_number,
    c.business_name,
    c.credit_score AS current_credit_score,
    rg_current.grade_code AS loan_risk_grade,
    rg_current.interest_rate AS current_rate,
    (SELECT rg2.grade_code
     FROM risk_grade rg2
     WHERE c.credit_score BETWEEN rg2.min_credit_score AND rg2.max_credit_score) AS qualified_grade,
    (SELECT rg2.interest_rate
     FROM risk_grade rg2
     WHERE c.credit_score BETWEEN rg2.min_credit_score AND rg2.max_credit_score) AS qualified_rate,
    l.outstanding_balance,
    l.term_months,
    ROUND(l.outstanding_balance * (rg_current.interest_rate -
          (SELECT rg2.interest_rate FROM risk_grade rg2
           WHERE c.credit_score BETWEEN rg2.min_credit_score AND rg2.max_credit_score)) / 100, 2) AS potential_annual_savings
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN risk_grade rg_current ON l.risk_grade_id = rg_current.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE ls.status_code = 'CURRENT'
  AND l.outstanding_balance > 50000
  AND c.credit_score > rg_current.max_credit_score + 10
ORDER BY potential_annual_savings DESC
LIMIT 30;
```

**Expected Result Description:**
Returns current loans where the customer's credit score now exceeds their original risk grade's maximum by at least 10 points, indicating qualification for a better grade. Shows potential annual interest savings if refinanced. Customers saving >$2,000/year are high-priority outreach targets. The Relationship Manager calls these customers to offer refinancing, improving retention and demonstrating that Pacific Bridge rewards good payment behavior.

---

### Query 17: Monthly Cash Flow Projection

**Business Context:**
The CFO needs to forecast monthly cash inflows from loan repayments for the next 12 months to manage the company's liquidity and funding needs. Pacific Bridge funds its loans through a credit facility that requires maintaining minimum cash reserves. By projecting scheduled payments from the existing portfolio, the CFO can determine when to draw on the credit line, when to pay it down, and how much capacity exists for new loan originations. Missing cash flow projections could lead to liquidity crunches or expensive emergency borrowing.

**Category:** Aggregation + Date
**Difficulty:** Intermediate
**Business Role:** Finance

```sql
-- Project expected monthly cash inflows from scheduled loan repayments
SELECT
    strftime('%Y-%m', rs.due_date) AS month,
    COUNT(DISTINCT rs.loan_id) AS loans_with_payments_due,
    COUNT(rs.id) AS total_installments_due,
    ROUND(SUM(rs.scheduled_payment), 2) AS expected_total_payment,
    ROUND(SUM(rs.principal_portion), 2) AS expected_principal,
    ROUND(SUM(rs.interest_portion), 2) AS expected_interest,
    ROUND(AVG(rs.scheduled_payment), 2) AS avg_payment_per_loan
FROM repayment_schedule rs
JOIN loan l ON rs.loan_id = l.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE rs.due_date BETWEEN DATE('now') AND DATE('now', '+12 months')
  AND ls.status_code IN ('CURRENT', 'DISBURSED')
GROUP BY month
ORDER BY month ASC;
```

**Expected Result Description:**
Returns 12-month forward-looking projection of expected payments broken down by principal and interest components. Shows total expected inflows and number of active loans. The CFO compares this to committed new loan disbursements (outflows) to calculate net cash position. If any month shows net negative cash, the company needs to arrange funding in advance. This projection updates weekly as new loans are disbursed and old loans mature.

---

### Query 18: Application Processing Time Analysis

**Business Context:**
The VP of Operations set a goal to respond to loan applications within 7 business days. Slow turnaround times hurt customer satisfaction and increase the risk that applicants shop with competitors. This analysis measures the time between application submission and decision (approval/rejection) to identify bottlenecks. If certain loan officers or industries consistently take longer to process, the operations team can investigate whether it's due to complexity, workload imbalance, or inefficiency. Improving turnaround from 10 days to 5 days could increase approval-to-funding conversion by 15%.

**Category:** Date Calculation
**Difficulty:** Basic
**Business Role:** Operations

```sql
-- Measure application processing times from submission to decision
SELECT
    lo.employee_id,
    lo.first_name || ' ' || lo.last_name AS officer_name,
    COUNT(a.id) AS applications_processed,
    ROUND(AVG(JULIANDAY(a.decision_date) - JULIANDAY(a.application_date)), 1) AS avg_days_to_decision,
    MIN(JULIANDAY(a.decision_date) - JULIANDAY(a.application_date)) AS min_days,
    MAX(JULIANDAY(a.decision_date) - JULIANDAY(a.application_date)) AS max_days,
    COUNT(CASE WHEN JULIANDAY(a.decision_date) - JULIANDAY(a.application_date) <= 7 THEN 1 END) AS within_sla,
    ROUND(100.0 * COUNT(CASE WHEN JULIANDAY(a.decision_date) - JULIANDAY(a.application_date) <= 7 THEN 1 END) / COUNT(a.id), 2) AS sla_compliance_pct
FROM application a
JOIN loan_officer lo ON a.loan_officer_id = lo.id
WHERE a.decision_date IS NOT NULL
  AND a.application_date IS NOT NULL
GROUP BY lo.id, lo.employee_id, lo.first_name, lo.last_name
HAVING applications_processed >= 20
ORDER BY avg_days_to_decision DESC;
```

**Expected Result Description:**
Returns turnaround time metrics by loan officer showing average, min, and max days from application to decision, plus SLA compliance percentage. Officers with avg_days_to_decision > 10 or SLA compliance < 70% need coaching or workload rebalancing. The operations team tracks this monthly and sets individual performance targets. Industry benchmark is 5-7 days, so Pacific Bridge aims for 90%+ SLA compliance.

---

### Query 19: Industry-Specific Default Patterns

**Business Context:**
The Chief Risk Officer is preparing for an investor meeting where she must explain the portfolio's industry exposures and associated risks. Investors are particularly concerned about cyclical industries like restaurants and hospitality that struggled during the pandemic. This query analyzes default rates, loss severity, and concentration for each industry, allowing the CRO to explain which industries pose the greatest risk and what actions are being taken (sector caps, higher pricing, enhanced monitoring). Showing proactive risk management reassures investors and maintains funding costs.

**Category:** CTE + Aggregation
**Difficulty:** Advanced
**Business Role:** Executive

```sql
-- Deep dive into default patterns and losses by industry
WITH industry_performance AS (
    SELECT
        i.industry_name,
        i.default_rate_baseline,
        COUNT(DISTINCT l.id) AS total_loans,
        ROUND(SUM(l.approved_amount), 2) AS total_originated,
        ROUND(SUM(l.outstanding_balance), 2) AS current_outstanding,
        COUNT(de.id) AS defaults,
        ROUND(100.0 * COUNT(de.id) / COUNT(DISTINCT l.id), 2) AS actual_default_rate_pct,
        ROUND(SUM(de.loss_amount), 2) AS total_losses,
        ROUND(AVG(de.loss_amount), 2) AS avg_loss_per_default
    FROM industry i
    JOIN customer c ON i.id = c.industry_id
    LEFT JOIN loan l ON c.id = l.customer_id
    LEFT JOIN default_event de ON l.id = de.loan_id
    GROUP BY i.id, i.industry_name, i.default_rate_baseline
)
SELECT
    industry_name,
    default_rate_baseline AS historical_baseline_pct,
    total_loans,
    current_outstanding,
    ROUND(100.0 * current_outstanding / (SELECT SUM(current_outstanding) FROM industry_performance), 2) AS pct_of_portfolio,
    defaults,
    actual_default_rate_pct,
    ROUND(actual_default_rate_pct - default_rate_baseline, 2) AS performance_vs_baseline,
    total_losses,
    avg_loss_per_default
FROM industry_performance
WHERE total_loans > 0
ORDER BY current_outstanding DESC;
```

**Expected Result Description:**
Returns comprehensive industry performance metrics showing current exposure, default rates compared to historical baselines, total losses, and average loss per default. Industries with actual_default_rate significantly above baseline (e.g., Hospitality at 15% vs 12.4% baseline) are underperforming and may require pricing adjustments or exposure caps. The CRO uses this table to demonstrate to investors that the company understands its industry risks and actively manages concentrations.

---

### Query 20: Customer Segmentation by Lifetime Value

**Business Context:**
The CEO wants to implement a tiered customer service model where high-value customers receive white-glove treatment (dedicated account managers, priority processing) while lower-value customers use self-service channels. This segmentation analysis calculates lifetime value (LTV) for each customer based on total loan volume, interest paid, and default history. Customers with $500K+ total borrowing and zero defaults are "platinum" tier, while one-time borrowers with <$100K are "standard" tier. This informs resource allocation for relationship management and customer success teams.

**Category:** CTE + Window Function
**Difficulty:** Advanced
**Business Role:** Executive

```sql
-- Segment customers by lifetime value and assign tiers
WITH customer_metrics AS (
    SELECT
        c.id AS customer_id,
        c.business_name,
        c.is_repeat_customer,
        COUNT(DISTINCT l.id) AS total_loans,
        ROUND(SUM(l.approved_amount), 2) AS total_borrowed,
        ROUND(SUM(l.approved_amount * l.interest_rate / 100 * l.term_months / 12), 2) AS estimated_lifetime_interest,
        COUNT(de.id) AS defaults,
        ROUND(SUM(CASE WHEN ls.status_code = 'PAID_OFF' THEN 1 ELSE 0 END) * 100.0 / COUNT(l.id), 2) AS completion_rate_pct,
        ROUND(AVG(l.interest_rate), 2) AS avg_interest_rate
    FROM customer c
    LEFT JOIN loan l ON c.id = l.customer_id
    LEFT JOIN loan_status ls ON l.current_status_id = ls.id
    LEFT JOIN default_event de ON l.id = de.loan_id
    GROUP BY c.id, c.business_name, c.is_repeat_customer
    HAVING total_loans > 0
),
customer_ltv AS (
    SELECT
        *,
        ROUND(total_borrowed + estimated_lifetime_interest - (defaults * 50000), 2) AS lifetime_value_score
    FROM customer_metrics
)
SELECT
    customer_id,
    business_name,
    total_loans,
    total_borrowed,
    estimated_lifetime_interest,
    defaults,
    lifetime_value_score,
    CASE
        WHEN lifetime_value_score >= 500000 AND defaults = 0 THEN 'Platinum'
        WHEN lifetime_value_score >= 250000 AND defaults = 0 THEN 'Gold'
        WHEN lifetime_value_score >= 100000 OR is_repeat_customer = 1 THEN 'Silver'
        ELSE 'Standard'
    END AS customer_tier,
    NTILE(10) OVER (ORDER BY lifetime_value_score DESC) AS ltv_decile
FROM customer_ltv
ORDER BY lifetime_value_score DESC
LIMIT 100;
```

**Expected Result Description:**
Returns top 100 customers ranked by lifetime value score (total borrowing + interest - default losses), assigned to customer tiers (Platinum/Gold/Silver/Standard). Platinum customers (top 5-10%) receive dedicated account managers and proactive refinancing offers. Standard tier uses digital self-service. This segmentation drives the customer success team's resource allocation and determines who gets invited to exclusive events, early access to new products, and other VIP treatment.

---

## Query Categories Summary

| Category | Count | Query Numbers |
|----------|-------|---------------|
| Aggregation | 10 | 1, 2, 5, 6, 7, 10, 11, 15, 17, 18 |
| Join Operations | 15 | 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 16, 19, 20 |
| Window Functions | 3 | 4, 14, 20 |
| Date/Time Analysis | 6 | 6, 13, 14, 17, 18 |
| Subqueries/CTEs | 8 | 3, 8, 9, 12, 16, 19, 20 |

## Business Role Coverage

| Role | Count | Query Numbers |
|------|-------|---------------|
| Executive/C-Level | 5 | 1, 2, 5, 19, 20 |
| Manager | 5 | 2, 7, 12, 16 |
| Analyst | 6 | 3, 4, 8, 13, 15 |
| Operations | 4 | 6, 9, 14, 18 |
| Finance | 4 | 10, 11, 17 |

## Difficulty Distribution

| Difficulty | Count | Query Numbers |
|------------|-------|---------------|
| Basic | 5 | 6, 11, 15, 18 |
| Intermediate | 9 | 1, 2, 5, 7, 10, 13, 14, 17 |
| Advanced | 6 | 3, 4, 8, 12, 16, 19, 20 |

---

## Notes

- All queries are designed to work with SQLite 3.x syntax
- Date calculations use `JULIANDAY()` and `strftime()` functions (SQLite-specific)
- For PostgreSQL, replace `JULIANDAY()` differences with date subtraction and `strftime()` with `TO_CHAR()`
- For MySQL, use `DATEDIFF()` and `DATE_FORMAT()` instead
- Queries reference the TSV file topological order (01-10) which determines safe loading sequence
- All currency amounts are in USD with 2 decimal precision
- Queries are designed to answer the 5 core business questions from the Pacific Bridge Lending consulting project

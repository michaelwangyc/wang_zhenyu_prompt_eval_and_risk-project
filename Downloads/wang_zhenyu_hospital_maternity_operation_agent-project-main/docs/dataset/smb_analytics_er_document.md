# FinTech - SMB Lending Pipeline

## Business Context

Pacific Bridge Lending is a California-based mid-sized fintech company specializing in small-to-medium business loans. This dataset models their complete lending pipeline from initial application through disbursement, repayment, and potential default. The data supports comprehensive analysis of five critical business problems: (1) risk pricing alignment between risk grades and actual default rates, (2) portfolio concentration risk across industries, (3) approval leakage where good customers are falsely rejected, (4) early warning signals that predict defaults before they occur, and (5) customer lifecycle value comparing repeat versus first-time borrowers. The dataset covers approximately 2 years of operations with realistic distributions across California markets, industries, and risk tiers.

## Complexity Level: Medium

- **Tables:** 10 tables
- **Total Records:** ~52,500 rows
- **Relationships:** 12 foreign key relationships (9 one-to-many, 0 many-to-many, plus 3 enum/lookup references)

---

## Entity Relationship Diagram

```mermaid
erDiagram
    industry ||--o{ customer : "classifies"
    customer ||--o{ application : "submits"
    customer ||--o{ loan : "receives"
    loan_officer ||--o{ application : "handles"
    loan_status ||--o{ application : "tracks"
    loan_status ||--o{ loan : "tracks"
    risk_grade ||--o{ loan : "assigns"
    application ||--|| loan : "approved as"
    loan ||--o{ repayment_schedule : "has"
    loan ||--o{ payment : "receives"
    loan ||--o| default_event : "may have"

    industry {
        int id PK
        string industry_code UK
        string industry_name
        float default_rate_baseline
    }

    risk_grade {
        int id PK
        string grade_code UK
        string grade_name
        int min_credit_score
        int max_credit_score
        float interest_rate
        float implied_default_rate
    }

    loan_status {
        int id PK
        string status_code UK
        string status_name
        string status_category
    }

    loan_officer {
        int id PK
        string employee_id UK
        string first_name
        string last_name
        string email
        date hire_date
        string region
    }

    customer {
        int id PK
        string business_name
        string tax_id UK
        int industry_id FK
        string state
        string city
        int founded_year
        decimal annual_revenue
        int employee_count
        int credit_score
        date first_contact_date
        boolean is_repeat_customer
    }

    application {
        int id PK
        string application_number UK
        int customer_id FK
        int loan_officer_id FK
        decimal requested_amount
        int requested_term_months
        date application_date
        date decision_date
        int status_id FK
        string rejection_reason
    }

    loan {
        int id PK
        string loan_number UK
        int application_id FK UK
        int customer_id FK
        int risk_grade_id FK
        decimal approved_amount
        float interest_rate
        int term_months
        decimal monthly_payment
        date disbursement_date
        date maturity_date
        int current_status_id FK
        decimal outstanding_balance
    }

    repayment_schedule {
        int id PK
        int loan_id FK
        int installment_number
        date due_date
        decimal scheduled_payment
        decimal principal_portion
        decimal interest_portion
        decimal remaining_balance
    }

    payment {
        int id PK
        int loan_id FK
        date payment_date
        decimal payment_amount
        int installment_number
        int days_late
        string payment_method
    }

    default_event {
        int id PK
        int loan_id FK UK
        date default_date
        int installments_missed
        decimal outstanding_at_default
        decimal recovery_amount
        decimal loss_amount
        boolean had_early_warning
        string warning_signals
    }
```

---

## Table Definitions

### 1. industry

**Description:** Industry classification for business borrowers. Each industry has a historical baseline default rate used for portfolio risk assessment and concentration analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| industry_code | VARCHAR(20) | NOT NULL, UNIQUE | Short industry code (e.g., REST, TECH) |
| industry_name | VARCHAR(100) | NOT NULL | Full industry name |
| default_rate_baseline | FLOAT | NOT NULL | Historical default rate percentage |

**Foreign Keys:** None (lookup table)

**Sample Data:**

| id | industry_code | industry_name | default_rate_baseline |
|----|---------------|---------------|----------------------|
| 1 | REST | Restaurant | 9.5 |
| 2 | RETAIL | Retail | 8.2 |
| 3 | TECH | Technology Services | 4.1 |
| 11 | HOSPIT | Hospitality | 12.4 |

---

### 2. risk_grade

**Description:** Risk grade tiers (A through E) used for loan pricing and credit assessment. Each grade has a credit score range, assigned interest rate, and implied default rate used in pricing calculations. Critical for analyzing risk pricing misalignment (Q1).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| grade_code | VARCHAR(10) | NOT NULL, UNIQUE | Grade letter (A, B, C, D, E) |
| grade_name | VARCHAR(50) | NOT NULL | Grade description (Prime, Near Prime, etc.) |
| min_credit_score | INTEGER | NOT NULL | Minimum credit score for this grade |
| max_credit_score | INTEGER | NOT NULL | Maximum credit score for this grade |
| interest_rate | FLOAT | NOT NULL | Annual interest rate percentage |
| implied_default_rate | FLOAT | NOT NULL | Expected default rate used in pricing |

**Foreign Keys:** None (lookup table)

**Sample Data:**

| id | grade_code | grade_name | min_credit_score | max_credit_score | interest_rate | implied_default_rate |
|----|------------|------------|------------------|------------------|---------------|---------------------|
| 1 | A | Prime | 720 | 850 | 5.5 | 3.0 |
| 2 | B | Near Prime | 680 | 719 | 7.5 | 6.0 |
| 3 | C | Standard | 640 | 679 | 9.5 | 6.0 |

**Note:** Grade C is intentionally mispriced (implied default 6.0%, actual ~11.2%) to support Q1 analysis.

---

### 3. loan_status

**Description:** Lifecycle status codes for loan applications and active loans. Organized into three categories: Application (pending review, approved, rejected), Active (disbursed, current), and Closed (defaulted, paid off).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| status_code | VARCHAR(20) | NOT NULL, UNIQUE | Status code identifier |
| status_name | VARCHAR(50) | NOT NULL | Display name |
| status_category | VARCHAR(20) | NOT NULL | Category: Application, Active, or Closed |

**Foreign Keys:** None (lookup table)

**Sample Data:**

| id | status_code | status_name | status_category |
|----|-------------|-------------|-----------------|
| 3 | APPROVED | Approved | Application |
| 4 | REJECTED | Rejected | Application |
| 6 | CURRENT | Current | Active |
| 7 | DEFAULTED | Defaulted | Closed |

---

### 4. loan_officer

**Description:** Loan officers who process and manage loan applications. Each officer is assigned to a California region and handles multiple applications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| employee_id | VARCHAR(20) | NOT NULL, UNIQUE | Employee identifier (LO####) |
| first_name | VARCHAR(50) | NOT NULL | Officer first name |
| last_name | VARCHAR(50) | NOT NULL | Officer last name |
| email | VARCHAR(100) | NOT NULL | Corporate email address |
| hire_date | DATE | NOT NULL | Employment start date |
| region | VARCHAR(50) | NOT NULL | Assigned region (Northern CA, Southern CA, etc.) |

**Foreign Keys:** None

**Sample Data:**

| id | employee_id | first_name | last_name | email | hire_date | region |
|----|-------------|------------|-----------|-------|-----------|--------|
| 1 | LO0001 | Sarah | Johnson | lo0001@pacificbridge.com | 2020-03-15 | Bay Area |
| 2 | LO0002 | Michael | Chen | lo0002@pacificbridge.com | 2019-08-22 | Southern CA |

---

### 5. customer

**Description:** Business borrowers seeking loans. Each customer is a small-to-medium business in California with financial characteristics including annual revenue, employee count, and credit score. The is_repeat_customer flag identifies customers who have returned for additional loans, critical for Q5 lifecycle analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| business_name | VARCHAR(200) | NOT NULL | Legal business name |
| tax_id | VARCHAR(20) | NOT NULL, UNIQUE | Federal tax ID (EIN) |
| industry_id | INTEGER | FK → industry.id | Business industry classification |
| state | VARCHAR(2) | NOT NULL | State code (always CA) |
| city | VARCHAR(100) | NOT NULL | City location |
| founded_year | INTEGER | NOT NULL | Year business was founded |
| annual_revenue | NUMERIC(12,2) | NOT NULL | Annual revenue in USD |
| employee_count | INTEGER | NOT NULL | Number of employees |
| credit_score | INTEGER | NOT NULL | Business credit score (300-850) |
| first_contact_date | DATE | NOT NULL | Date of first interaction with Pacific Bridge |
| is_repeat_customer | BOOLEAN | DEFAULT FALSE | True if customer has multiple loans |

**Foreign Keys:**
- `industry_id` → `industry.id` (ON DELETE RESTRICT)

**Sample Data:**

| id | business_name | tax_id | industry_id | city | credit_score | is_repeat_customer |
|----|---------------|--------|-------------|------|--------------|-------------------|
| 1 | Golden Dragon Restaurant | 94-1234567 | 1 | San Francisco | 685 | false |
| 2 | TechVentures LLC | 94-7654321 | 3 | San Jose | 742 | true |

---

### 6. application

**Description:** Loan applications submitted by customers. Each application tracks the requested amount, term, processing timeline, and decision outcome (approved or rejected). The rejection_reason field provides insights for Q3 approval leakage analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| application_number | VARCHAR(50) | NOT NULL, UNIQUE | Application identifier (APP-######) |
| customer_id | INTEGER | FK → customer.id | Applicant business |
| loan_officer_id | INTEGER | FK → loan_officer.id | Assigned loan officer |
| requested_amount | NUMERIC(12,2) | NOT NULL | Requested loan amount in USD |
| requested_term_months | INTEGER | NOT NULL | Requested loan term (12, 24, 36, 48, 60) |
| application_date | DATE | NOT NULL | Date application was submitted |
| decision_date | DATE | NULL | Date approval/rejection decision was made |
| status_id | INTEGER | FK → loan_status.id | Current application status |
| rejection_reason | VARCHAR(200) | NULL | Reason for rejection if applicable |

**Foreign Keys:**
- `customer_id` → `customer.id` (ON DELETE RESTRICT)
- `loan_officer_id` → `loan_officer.id` (ON DELETE RESTRICT)
- `status_id` → `loan_status.id` (ON DELETE RESTRICT)

**Sample Data:**

| id | application_number | customer_id | requested_amount | application_date | status_id | rejection_reason |
|----|-------------------|-------------|------------------|------------------|-----------|------------------|
| 1 | APP-000001 | 1 | 150000.00 | 2024-01-15 | 3 | NULL |
| 2 | APP-000002 | 45 | 250000.00 | 2024-01-16 | 4 | DTI ratio too high |

---

### 7. loan

**Description:** Approved and disbursed loans. Each loan is linked to exactly one application and includes final approved terms, assigned risk grade, payment schedule details, and current repayment status. The outstanding_balance tracks remaining principal.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| loan_number | VARCHAR(50) | NOT NULL, UNIQUE | Loan identifier (LN-######) |
| application_id | INTEGER | FK → application.id, UNIQUE | Source application (1:1 relationship) |
| customer_id | INTEGER | FK → customer.id | Borrower |
| risk_grade_id | INTEGER | FK → risk_grade.id | Assigned risk grade |
| approved_amount | NUMERIC(12,2) | NOT NULL | Disbursed loan amount |
| interest_rate | FLOAT | NOT NULL | Annual interest rate percentage |
| term_months | INTEGER | NOT NULL | Loan term in months |
| monthly_payment | NUMERIC(10,2) | NOT NULL | Required monthly payment amount |
| disbursement_date | DATE | NOT NULL | Date funds were disbursed |
| maturity_date | DATE | NOT NULL | Expected final payment date |
| current_status_id | INTEGER | FK → loan_status.id | Current loan status |
| outstanding_balance | NUMERIC(12,2) | NOT NULL | Remaining principal balance |

**Foreign Keys:**
- `application_id` → `application.id` (ON DELETE RESTRICT)
- `customer_id` → `customer.id` (ON DELETE RESTRICT)
- `risk_grade_id` → `risk_grade.id` (ON DELETE RESTRICT)
- `current_status_id` → `loan_status.id` (ON DELETE RESTRICT)

**Sample Data:**

| id | loan_number | application_id | risk_grade_id | approved_amount | interest_rate | term_months | current_status_id |
|----|-------------|----------------|---------------|-----------------|---------------|-------------|------------------|
| 1 | LN-000001 | 1 | 2 | 145000.00 | 7.5 | 36 | 6 |
| 2 | LN-000002 | 5 | 1 | 225000.00 | 5.5 | 48 | 8 |

---

### 8. repayment_schedule

**Description:** Expected monthly payment schedule for each loan. Each row represents one monthly installment with scheduled payment amount broken down into principal and interest portions, plus remaining balance after payment. Used to compare against actual payment behavior.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| loan_id | INTEGER | FK → loan.id | Parent loan |
| installment_number | INTEGER | NOT NULL | Payment sequence number (1 to term_months) |
| due_date | DATE | NOT NULL | Payment due date |
| scheduled_payment | NUMERIC(10,2) | NOT NULL | Total amount due |
| principal_portion | NUMERIC(10,2) | NOT NULL | Principal component of payment |
| interest_portion | NUMERIC(10,2) | NOT NULL | Interest component of payment |
| remaining_balance | NUMERIC(12,2) | NOT NULL | Balance after this payment |

**Foreign Keys:**
- `loan_id` → `loan.id` (ON DELETE CASCADE)

**Sample Data:**

| id | loan_id | installment_number | due_date | scheduled_payment | principal_portion | interest_portion | remaining_balance |
|----|---------|-------------------|----------|-------------------|-------------------|------------------|-------------------|
| 1 | 1 | 1 | 2024-02-15 | 4488.20 | 3582.70 | 905.50 | 141417.30 |
| 2 | 1 | 2 | 2024-03-15 | 4488.20 | 3605.08 | 883.12 | 137812.22 |

---

### 9. payment

**Description:** Actual payments received from borrowers. Each payment records the date received, amount paid, associated installment number, and lateness in days. Payment behavior (on-time, late, partial) provides early warning signals for Q4 default prediction analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| loan_id | INTEGER | FK → loan.id | Parent loan |
| payment_date | DATE | NOT NULL | Date payment was received |
| payment_amount | NUMERIC(10,2) | NOT NULL | Amount paid |
| installment_number | INTEGER | NOT NULL | Which installment this payment covers |
| days_late | INTEGER | DEFAULT 0 | Number of days past due date (0 = on time) |
| payment_method | VARCHAR(50) | NOT NULL | ACH, Wire Transfer, Check, Credit Card |

**Foreign Keys:**
- `loan_id` → `loan.id` (ON DELETE CASCADE)

**Sample Data:**

| id | loan_id | payment_date | payment_amount | installment_number | days_late | payment_method |
|----|---------|--------------|----------------|-------------------|-----------|---------------|
| 1 | 1 | 2024-02-15 | 4488.20 | 1 | 0 | ACH |
| 2 | 1 | 2024-03-22 | 4488.20 | 2 | 7 | ACH |
| 3 | 5 | 2024-04-10 | 2800.00 | 3 | 25 | Check |

---

### 10. default_event

**Description:** Records of loan defaults with recovery information and early warning indicator analysis. Each defaulted loan has exactly one default event. The had_early_warning flag and warning_signals field document behavioral deterioration (late payments, partial payments) observed in the 3 months prior to default, supporting Q4 early warning analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Primary key |
| loan_id | INTEGER | FK → loan.id, UNIQUE | Defaulted loan (1:1 relationship) |
| default_date | DATE | NOT NULL | Date default was declared (90 days past due) |
| installments_missed | INTEGER | NOT NULL | Number of payments never made |
| outstanding_at_default | NUMERIC(12,2) | NOT NULL | Principal balance at default |
| recovery_amount | NUMERIC(12,2) | DEFAULT 0.00 | Amount recovered through collections |
| loss_amount | NUMERIC(12,2) | NOT NULL | Net loss after recovery |
| had_early_warning | BOOLEAN | DEFAULT FALSE | True if warning signals detected 3+ months prior |
| warning_signals | VARCHAR(500) | NULL | Description of warning signals observed |

**Foreign Keys:**
- `loan_id` → `loan.id` (ON DELETE RESTRICT)

**Sample Data:**

| id | loan_id | default_date | outstanding_at_default | recovery_amount | had_early_warning | warning_signals |
|----|---------|--------------|------------------------|-----------------|-------------------|-----------------|
| 1 | 87 | 2025-06-15 | 125000.00 | 45000.00 | true | 2 late payments in last 3 months; 1 partial payments |
| 2 | 142 | 2025-08-22 | 88500.00 | 28000.00 | false | NULL |

---

## Data Generation Rules

### Business Logic Constraints

1. **Temporal Ordering:**
   - `application.application_date` < `application.decision_date`
   - `application.decision_date` < `loan.disbursement_date` (for approved applications)
   - `loan.disbursement_date` < `loan.maturity_date`
   - `repayment_schedule.due_date` follows monthly cadence from `loan.disbursement_date`
   - `payment.payment_date` >= `repayment_schedule.due_date` (may be late)

2. **Referential Integrity:**
   - All applications must reference existing customers, loan officers, and statuses
   - Only approved applications (status_id = 3) generate loan records
   - Each loan has exactly one application (application_id is unique in loan table)
   - Defaulted loans (current_status_id = 7) must have a corresponding default_event record
   - Payment installment_number must match valid repayment_schedule entries

3. **Value Ranges:**
   - Credit scores: 300-850
   - Requested amounts: $50,000 - $500,000 (in $1,000 increments)
   - Loan terms: 12, 24, 36, 48, or 60 months only
   - Interest rates: 5.5% - 16.0% (based on risk grade)
   - Days late: 0-30 days (longer lateness triggers default)

4. **Computed Fields:**
   - `loan.monthly_payment` = calculated using amortization formula
   - `repayment_schedule.principal_portion` + `interest_portion` = `scheduled_payment`
   - `default_event.loss_amount` = `outstanding_at_default` - `recovery_amount`
   - `loan.outstanding_balance` = original amount minus sum of principal payments received

5. **Distribution Rules:**
   - 73% of applications are approved, 27% rejected
   - 10% of loans default, 20% paid off early, 70% remain current
   - 15% of customers are repeat customers (higher credit scores)
   - 72% of defaults have early warning signals
   - 70% of payments are on time, 20% late 1-15 days, 10% late 16-30 days
   - Industry distribution: Restaurants 18%, Technology 12%, Construction 10%, others distributed
   - Risk grade distribution: A: 20%, B: 30%, C: 25%, D: 20%, E: 5%

6. **Business Problem Embeddings:**
   - **Q1 Risk Pricing:** Grade C interest_rate set at 9.5% (implied default 6.0%) but actual defaults ~11.2%
   - **Q2 Portfolio Concentration:** Restaurant industry overrepresented in disbursed loans
   - **Q3 Approval Leakage:** ~23% of rejected applications have credit profiles similar to approved customers
   - **Q4 Early Warning:** 72% of defaults show late/partial payment patterns 3+ months before default
   - **Q5 Lifecycle Value:** Repeat customers (15%) have 3.2% default rate vs 9.1% for first-time customers

### Faker Strategies

| Field Pattern | Faker Method | Notes |
|---------------|--------------|-------|
| business_name | `fake.company()` | Company names |
| tax_id | `fake.bothify(text='##-#######')` | EIN format |
| person name | `fake.first_name()`, `fake.last_name()` | Loan officer names |
| email (corporate) | f"lo{id:04d}@pacificbridge.com" | Standardized corporate email |
| city | `random.choice(ca_cities)` | California cities only |
| phone | `fake.phone_number()` | US format |
| date (application) | `fake.date_between(start_date='-2y', end_date='-30d')` | Last 2 years, not recent |
| hire_date | `fake.date_between(start_date='-5y', end_date='-6m')` | Established employees |
| amounts | `random.randint(50, 500) * 1000` | Round thousands |
| credit_score | `random.randint(550, 820)` + adjustments | Business credit score range |

---

## File Manifest

| # | Filename | Table | Rows | Dependencies |
|---|----------|-------|------|--------------|
| 01 | 01_industry.tsv | industry | 15 | None |
| 02 | 02_risk_grade.tsv | risk_grade | 5 | None |
| 03 | 03_loan_status.tsv | loan_status | 8 | None |
| 04 | 04_loan_officer.tsv | loan_officer | 20 | None |
| 05 | 05_customer.tsv | customer | 800 | industry |
| 06 | 06_application.tsv | application | 3000 | customer, loan_officer, loan_status |
| 07 | 07_loan.tsv | loan | ~2190 | application, customer, risk_grade, loan_status |
| 08 | 08_repayment_schedule.tsv | repayment_schedule | ~26280 | loan |
| 09 | 09_payment.tsv | payment | ~18000 | loan, repayment_schedule |
| 10 | 10_default_event.tsv | default_event | ~220 | loan |

**Total Estimated Rows:** ~52,538

---

## Database Schema (SQLite DDL)

```sql
-- Lookup Tables

CREATE TABLE industry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_code VARCHAR(20) NOT NULL UNIQUE,
    industry_name VARCHAR(100) NOT NULL,
    default_rate_baseline REAL NOT NULL
);

CREATE TABLE risk_grade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade_code VARCHAR(10) NOT NULL UNIQUE,
    grade_name VARCHAR(50) NOT NULL,
    min_credit_score INTEGER NOT NULL,
    max_credit_score INTEGER NOT NULL,
    interest_rate REAL NOT NULL,
    implied_default_rate REAL NOT NULL
);

CREATE TABLE loan_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status_code VARCHAR(20) NOT NULL UNIQUE,
    status_name VARCHAR(50) NOT NULL,
    status_category VARCHAR(20) NOT NULL
);

-- Entities

CREATE TABLE loan_officer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name VARCHAR(200) NOT NULL,
    tax_id VARCHAR(20) NOT NULL UNIQUE,
    industry_id INTEGER NOT NULL,
    state VARCHAR(2) NOT NULL,
    city VARCHAR(100) NOT NULL,
    founded_year INTEGER NOT NULL,
    annual_revenue NUMERIC(12,2) NOT NULL,
    employee_count INTEGER NOT NULL,
    credit_score INTEGER NOT NULL,
    first_contact_date DATE NOT NULL,
    is_repeat_customer BOOLEAN DEFAULT 0,
    FOREIGN KEY (industry_id) REFERENCES industry(id)
);

CREATE TABLE application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    loan_officer_id INTEGER NOT NULL,
    requested_amount NUMERIC(12,2) NOT NULL,
    requested_term_months INTEGER NOT NULL,
    application_date DATE NOT NULL,
    decision_date DATE,
    status_id INTEGER NOT NULL,
    rejection_reason VARCHAR(200),
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    FOREIGN KEY (loan_officer_id) REFERENCES loan_officer(id),
    FOREIGN KEY (status_id) REFERENCES loan_status(id)
);

CREATE TABLE loan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_number VARCHAR(50) NOT NULL UNIQUE,
    application_id INTEGER NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    risk_grade_id INTEGER NOT NULL,
    approved_amount NUMERIC(12,2) NOT NULL,
    interest_rate REAL NOT NULL,
    term_months INTEGER NOT NULL,
    monthly_payment NUMERIC(10,2) NOT NULL,
    disbursement_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    current_status_id INTEGER NOT NULL,
    outstanding_balance NUMERIC(12,2) NOT NULL,
    FOREIGN KEY (application_id) REFERENCES application(id),
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    FOREIGN KEY (risk_grade_id) REFERENCES risk_grade(id),
    FOREIGN KEY (current_status_id) REFERENCES loan_status(id)
);

CREATE TABLE repayment_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    scheduled_payment NUMERIC(10,2) NOT NULL,
    principal_portion NUMERIC(10,2) NOT NULL,
    interest_portion NUMERIC(10,2) NOT NULL,
    remaining_balance NUMERIC(12,2) NOT NULL,
    FOREIGN KEY (loan_id) REFERENCES loan(id) ON DELETE CASCADE
);

CREATE TABLE payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL,
    payment_date DATE NOT NULL,
    payment_amount NUMERIC(10,2) NOT NULL,
    installment_number INTEGER NOT NULL,
    days_late INTEGER DEFAULT 0,
    payment_method VARCHAR(50) NOT NULL,
    FOREIGN KEY (loan_id) REFERENCES loan(id) ON DELETE CASCADE
);

CREATE TABLE default_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL UNIQUE,
    default_date DATE NOT NULL,
    installments_missed INTEGER NOT NULL,
    outstanding_at_default NUMERIC(12,2) NOT NULL,
    recovery_amount NUMERIC(12,2) DEFAULT 0.00,
    loss_amount NUMERIC(12,2) NOT NULL,
    had_early_warning BOOLEAN DEFAULT 0,
    warning_signals VARCHAR(500),
    FOREIGN KEY (loan_id) REFERENCES loan(id)
);

-- Recommended Indexes for Query Performance

CREATE INDEX idx_customer_industry ON customer(industry_id);
CREATE INDEX idx_customer_credit_score ON customer(credit_score);
CREATE INDEX idx_customer_repeat ON customer(is_repeat_customer);
CREATE INDEX idx_application_customer ON application(customer_id);
CREATE INDEX idx_application_status ON application(status_id);
CREATE INDEX idx_application_date ON application(application_date);
CREATE INDEX idx_loan_customer ON loan(customer_id);
CREATE INDEX idx_loan_risk_grade ON loan(risk_grade_id);
CREATE INDEX idx_loan_status ON loan(current_status_id);
CREATE INDEX idx_loan_disbursement_date ON loan(disbursement_date);
CREATE INDEX idx_repayment_schedule_loan ON repayment_schedule(loan_id);
CREATE INDEX idx_payment_loan ON payment(loan_id);
CREATE INDEX idx_payment_date ON payment(payment_date);
CREATE INDEX idx_default_loan ON default_event(loan_id);
```

---

## Usage Notes

This dataset is specifically designed to support the Pacific Bridge Lending consulting project's five core business questions:

1. **Risk Pricing Analysis:** Compare `risk_grade.implied_default_rate` against actual default rates calculated from `loan` and `default_event` tables, particularly for Grade C loans.

2. **Portfolio Concentration:** Analyze loan distribution across `industry` table, focusing on outstanding balances and default exposure by industry.

3. **Approval Leakage:** Examine rejected applications (`application.status_id = 4`) and compare customer profiles (`credit_score`, `annual_revenue`, `employee_count`) against approved applications to identify false negatives.

4. **Early Warning Signals:** Use `payment.days_late` and `payment.payment_amount` patterns in the 3+ months before `default_event.default_date` to identify predictive behaviors.

5. **Customer Lifecycle Value:** Compare performance metrics (default rates, loan amounts, approval rates) between `customer.is_repeat_customer = true` vs `false`.

The dataset is production-ready for SQL analysis, Tableau visualization, and machine learning model training. All foreign key constraints are enforced in the SQLite database for data integrity.

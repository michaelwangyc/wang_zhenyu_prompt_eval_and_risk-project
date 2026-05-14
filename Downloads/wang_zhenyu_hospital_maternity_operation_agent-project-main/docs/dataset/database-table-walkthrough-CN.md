# 数据库表结构讲解

本文档从业务角度讲解 SMB Lending Lens 项目的数据库结构。我们从最简单的表开始，逐步引导你理解整个贷款业务的数据模型。

---

## 业务背景

**Pacific Bridge Lending** 是一家位于加州的中型金融科技公司，专注于为中小企业 (SMB) 提供贷款服务。

**核心业务流程：**

```
企业客户 → 提交贷款申请 → 信贷审批 → 发放贷款 → 按月还款 → 正常结清 / 违约
```

**数据规模：**

- 10 张表，约 52,000 条记录
- 12 个外键关系
- 覆盖约 2 年的运营数据

---

## 表的依赖关系（从简单到复杂）

按「被依赖次数」从少到多排序，方便循序渐进理解：

| 层级 | 表名 | 记录数 | 依赖的表 | 说明 |
|------|------|--------|----------|------|
| **第一层：基础配置表** | | | | |
| 1 | `industry` | 15 | 无 | 行业分类 |
| 2 | `risk_grade` | 5 | 无 | 风险等级 (A-E) |
| 3 | `loan_status` | 8 | 无 | 状态枚举 |
| 4 | `loan_officer` | 20 | 无 | 信贷专员 |
| **第二层：核心实体** | | | | |
| 5 | `customer` | 800 | industry | 企业客户 |
| **第三层：业务流程** | | | | |
| 6 | `application` | 3,000 | customer, loan_officer, loan_status | 贷款申请 |
| 7 | `loan` | 2,185 | application, customer, risk_grade, loan_status | 已发放贷款 |
| **第四层：交易明细** | | | | |
| 8 | `repayment_schedule` | 78,996 | loan | 还款计划 |
| 9 | `payment` | 33,968 | loan | 实际还款记录 |
| 10 | `default_event` | 232 | loan | 违约事件 |

---

## 第一层：基础配置表（无依赖）

这些表是独立的「枚举表」或「配置表」，不依赖其他表，是整个数据模型的基础。

### 1. `industry` - 行业分类

定义企业所属行业，每个行业有历史基准违约率。

| id | industry_code | industry_name | default_rate_baseline |
|----|---------------|---------------|----------------------|
| 1 | REST | Restaurant | 9.5 |
| 2 | RETAIL | Retail | 8.2 |
| 3 | TECH | Technology Services | 4.1 |
| 4 | CONST | Construction | 11.3 |
| 5 | HEALTH | Healthcare Services | 5.8 |

**重点字段**：

- `default_rate_baseline` 是历史违约率基准，用于风险评估和投资组合分析
- 不同行业的风险差异很大：科技 4.1% vs 建筑 11.3%

---

### 2. `risk_grade` - 风险等级

定义 5 个风险等级（A-E），每个等级对应不同的信用评分区间、利率和预期违约率。

| id | grade_code | grade_name | min_credit_score | max_credit_score | interest_rate | implied_default_rate |
|----|------------|------------|------------------|------------------|---------------|---------------------|
| 1 | A | Prime | 720 | 850 | 5.5% | 3.0% |
| 2 | B | Near Prime | 680 | 719 | 7.5% | 6.0% |
| 3 | C | Standard | 640 | 679 | 9.5% | 6.0% |
| 4 | D | Subprime | 600 | 639 | 12.5% | 13.0% |
| 5 | E | Deep Subprime | 300 | 599 | 16.0% | 18.0% |

**业务洞察**：

- `implied_default_rate` 是定价时假设的违约率
- C 级故意设计为定价偏低（implied 6%，但实际约 11.2%），用于模拟「风险定价错位」分析场景

---

### 3. `loan_status` - 状态枚举

贯穿整个贷款生命周期的状态码，分三类。

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

**分类逻辑**：

- `Application` 阶段：申请审批中
- `Active` 阶段：贷款存续期
- `Closed` 阶段：已结束（正常结清或违约）

---

### 4. `loan_officer` - 信贷专员

处理贷款申请的员工信息。

| id | employee_id | first_name | last_name | hire_date | region |
|----|-------------|------------|-----------|-----------|--------|
| 1 | LO0001 | Danielle | Johnson | 2022-07-12 | Northern CA |
| 2 | LO0002 | Jeffrey | Doyle | 2024-07-14 | Northern CA |
| 3 | LO0003 | Patricia | Miller | 2023-04-06 | Bay Area |
| 4 | LO0004 | Anthony | Robinson | 2023-09-05 | Southern CA |
| 5 | LO0005 | Anthony | Gonzalez | 2024-05-26 | Southern CA |

**业务用途**：

- 用于分析各信贷专员的审批效率、违约率等绩效指标
- `region` 字段用于区域业绩分析

---

## 第二层：核心实体表

### 5. `customer` - 企业客户

贷款申请人，即中小企业。这是第一个有外键依赖的表。

| id | business_name | tax_id | industry_id | city | credit_score | is_repeat_customer |
|----|---------------|--------|-------------|------|--------------|-------------------|
| 1 | Watts, Robinson and Nguyen | 03-0564139 | 3 (TECH) | Sacramento | 553 | 0 |
| 2 | Lewis-Porter | 72-4238849 | 6 | Fresno | 722 | 0 |
| 3 | Ross, Robinson and Bright | 87-1012269 | 15 | Oakland | 685 | 0 |
| 4 | Carlson-Mcdonald | 48-0184514 | 1 (REST) | Sacramento | 700 | 0 |
| 5 | Smith-Bowen | 48-2814893 | 7 | San Jose | 698 | 0 |

**重点字段**：

- `credit_score`：企业信用评分（300-850），决定风险等级
- `is_repeat_customer`：是否回头客（用于分析客户终身价值）
- `industry_id` → 外键关联 `industry` 表

**外键关系**：

```
customer.industry_id → industry.id
```

---

## 第三层：业务流程表

这一层的表记录了贷款业务的核心流程：从申请到放款。

### 6. `application` - 贷款申请

记录每笔贷款申请的详细信息。这是业务流程的起点。

| id | application_number | customer_id | loan_officer_id | requested_amount | application_date | status_id | rejection_reason |
|----|-------------------|-------------|-----------------|------------------|------------------|-----------|------------------|
| 1 | APP-000001 | 412 | 6 | $323,000 | 2024-05-10 | 3 (APPROVED) | |
| 2 | APP-000002 | 454 | 18 | $216,000 | 2024-07-23 | 4 (REJECTED) | Industry risk concentration |
| 3 | APP-000003 | 783 | 11 | $361,000 | 2024-03-04 | 4 (REJECTED) | Collateral insufficient |
| 4 | APP-000004 | 559 | 18 | $431,000 | 2025-11-24 | 3 (APPROVED) | |
| 5 | APP-000005 | 369 | 13 | $50,000 | 2024-07-06 | 3 (APPROVED) | |

**重点字段**：

- `rejection_reason`：拒绝原因，可用于「审批漏失分析」——找出被错误拒绝的优质客户
- 约 73% 的申请会被批准，27% 被拒绝

**外键关系**：

```
application.customer_id → customer.id
application.loan_officer_id → loan_officer.id
application.status_id → loan_status.id
```

---

### 7. `loan` - 已发放贷款

只有审批通过的申请才会生成贷款记录。与 `application` 是 **1:1 关系**。

| id | loan_number | application_id | customer_id | risk_grade_id | approved_amount | interest_rate | term_months | current_status_id |
|----|-------------|----------------|-------------|---------------|-----------------|---------------|-------------|------------------|
| 1 | LN-000001 | 1 | 412 | 2 (B级) | $321,013 | 7.5% | 60 | 6 (CURRENT) |
| 2 | LN-000002 | 4 | 559 | 1 (A级) | $425,447 | 5.5% | 36 | 8 (PAID_OFF) |
| 3 | LN-000003 | 5 | 369 | 5 (E级) | $48,534 | 16.0% | 12 | 6 (CURRENT) |
| 4 | LN-000004 | 6 | 292 | 4 (D级) | $52,431 | 12.5% | 36 | 6 (CURRENT) |
| 5 | LN-000005 | 8 | 524 | 1 (A级) | $117,690 | 5.5% | 12 | 6 (CURRENT) |

**重点字段**：

- `approved_amount`：实际批准金额（可能与申请金额不同）
- `interest_rate`：根据风险等级确定的年利率
- `term_months`：贷款期限（12/24/36/48/60 个月）

**外键关系（最复杂的表）**：

```
loan.application_id → application.id (UNIQUE, 1:1)
loan.customer_id → customer.id
loan.risk_grade_id → risk_grade.id
loan.current_status_id → loan_status.id
```

---

## 第四层：交易明细表

这些表记录贷款发放后的具体交易数据，都依赖于 `loan` 表。

### 8. `repayment_schedule` - 还款计划

每笔贷款的月度还款计划，详细到本金和利息拆分。**记录数最多**（78,996 条）。

| id | loan_id | installment_number | due_date | scheduled_payment | principal_portion | interest_portion | remaining_balance |
|----|---------|-------------------|----------|-------------------|-------------------|------------------|-------------------|
| 1 | 1 | 1 | 2024-07-08 | $6,432.44 | $4,426.11 | $2,006.33 | $316,586.94 |
| 2 | 1 | 2 | 2024-08-07 | $6,432.44 | $4,453.77 | $1,978.67 | $312,133.17 |
| 3 | 1 | 3 | 2024-09-06 | $6,432.44 | $4,481.61 | $1,950.83 | $307,651.56 |
| 4 | 1 | 4 | 2024-10-06 | $6,432.44 | $4,509.62 | $1,922.82 | $303,141.94 |
| 5 | 1 | 5 | 2024-11-05 | $6,432.44 | $4,537.80 | $1,894.64 | $298,604.14 |

**重点字段**：

- `principal_portion` + `interest_portion` = `scheduled_payment`
- `remaining_balance`：该期还款后的剩余本金
- 每笔贷款按期限生成 12-60 条还款计划

**外键关系**：

```
repayment_schedule.loan_id → loan.id
```

---

### 9. `payment` - 实际还款记录

记录客户实际支付的还款，包括逾期天数。这是「早期预警分析」的核心数据源。

| id | loan_id | payment_date | payment_amount | installment_number | days_late | payment_method |
|----|---------|--------------|----------------|-------------------|-----------|---------------|
| 1 | 1 | 2024-07-08 | $6,432.44 | 1 | 0 | Wire Transfer |
| 2 | 1 | 2024-08-15 | $4,163.11 | 2 | 8 | Check |
| 3 | 1 | 2024-09-16 | $6,432.44 | 3 | 10 | Credit Card |
| 4 | 1 | 2024-10-06 | $6,432.44 | 4 | 0 | Wire Transfer |
| 5 | 1 | 2024-11-05 | $6,432.44 | 5 | 0 | Wire Transfer |

**重点字段**：

- `days_late`：逾期天数（0 = 按时）
- 可以发现第 2 期还款金额不足（$4,163 < $6,432），且逾期 8 天——这是早期预警信号

**业务洞察**：

- 约 70% 的还款按时，20% 逾期 1-15 天，10% 逾期 16-30 天
- 逾期和部分还款模式是预测违约的关键指标

**外键关系**：

```
payment.loan_id → loan.id
```

---

### 10. `default_event` - 违约事件

记录违约贷款的详细信息，包括损失和预警信号。与 `loan` 是 **1:1 关系**（一笔贷款最多一个违约事件）。

| id | loan_id | default_date | installments_missed | outstanding_at_default | recovery_amount | loss_amount | had_early_warning | warning_signals |
|----|---------|--------------|---------------------|------------------------|-----------------|-------------|-------------------|-----------------|
| 1 | 14 | 2025-09-07 | 54 | $107,544 | $51,387 | $56,157 | 0 | |
| 2 | 24 | 2025-10-03 | 7 | $90,597 | $25,863 | $64,734 | 1 | 1 late payments in last 3 months |
| 3 | 27 | 2026-01-29 | 8 | $234,780 | $103,963 | $130,817 | 1 | 1 late payments; 1 partial payments |
| 4 | 35 | 2026-06-28 | 14 | $63,877 | $13,600 | $50,277 | 1 | 2 late payments; 1 partial payments |
| 5 | 37 | 2026-09-12 | 15 | $104,201 | $40,455 | $63,746 | 0 | |

**重点字段**：

- `had_early_warning`：是否有早期预警信号（约 72% 的违约有预警）
- `warning_signals`：具体预警信号描述
- `loss_amount` = `outstanding_at_default` - `recovery_amount`

**外键关系**：

```
default_event.loan_id → loan.id (UNIQUE, 1:1)
```

---

## 表之间的关系图

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

## 核心业务分析场景

这套数据专门设计用于 5 个关键业务分析：

| # | 分析场景 | 核心表 | 业务问题 |
|---|----------|--------|----------|
| Q1 | 风险定价错位分析 | risk_grade + loan + default_event | C 级贷款是否定价过低？ |
| Q2 | 投资组合集中度分析 | industry + loan | 餐饮业敞口是否过高？ |
| Q3 | 审批漏失分析 | application + customer | 有多少优质客户被错误拒绝？ |
| Q4 | 违约预警信号分析 | payment + default_event | 能否提前 3 个月预测违约？ |
| Q5 | 客户终身价值对比 | customer + loan | 回头客 vs 新客户哪个更值得投资？ |

---

## 要点总结

1. **第一层**是 4 张独立的「枚举/配置表」，定义业务规则
2. **`customer`** 是核心实体，连接行业分类
3. **`application` → `loan`** 是业务流程的关键转化点（只有 APPROVED 才会生成 loan）
4. **`loan`** 是数据的「枢纽」，往下分出三条分支：
   - `repayment_schedule`：应还款项
   - `payment`：实际还款
   - `default_event`：违约记录
5. 通过对比 `repayment_schedule` 和 `payment`，可以分析还款行为模式

---

## 高级分析概念

本节介绍通过多表 JOIN 或计算得出的业务指标。这些概念不存在于单独的表中，而是通过 SQL 查询「推导」出来的。

### 概念索引

| 概念 | 中文名 | 涉及的表 | 业务用途 |
|------|--------|----------|----------|
| Actual Default Rate | 实际违约率 | loan + default_event | 风险评估 |
| Pricing Gap | 定价差距 | risk_grade + loan + default_event | 定价校准 |
| Approval Rate | 审批通过率 | application + loan_status | 运营效率 |
| False Rejection | 误拒/审批漏失 | application + customer | 收入优化 |
| Late Payment Rate | 逾期率 | payment | 风险监控 |
| Partial Payment | 部分还款 | payment + loan | 早期预警 |
| Recovery Rate | 回收率 | default_event | 损失评估 |
| Loss Severity | 损失严重程度 | default_event | 拨备计算 |
| Expected Loss | 预期损失 | loan + risk_grade | 风险敞口 |
| Portfolio Concentration | 投资组合集中度 | loan + customer + industry | 分散化分析 |
| Days to Decision | 审批周期 | application | SLA 监控 |
| Payment Behavior Cohort | 还款行为队列 | payment + loan | 风险分群 |
| Customer LTV | 客户终身价值 | customer + loan + default_event | 客户分层 |
| Vintage Analysis | 年份分析 | loan + default_event | 趋势追踪 |
| Risk Grade Migration | 风险等级迁移 | customer + loan + risk_grade | 再融资机会 |

---

### 1. Actual Default Rate（实际违约率）

**定义**：已发放贷款中实际违约的比例。

**计算公式**：`违约贷款数 / 总贷款数 × 100%`

**涉及的表和字段**：
- `loan` 表：统计总贷款数
- `default_event` 表：统计违约数

**简化 SQL**：

```sql
SELECT
    COUNT(de.id) AS 违约数,
    COUNT(l.id) AS 总贷款数,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS 实际违约率
FROM loan l
LEFT JOIN default_event de ON l.id = de.loan_id;
```

**业务意义**：与 `risk_grade.implied_default_rate`（定价假设违约率）对比，判断定价是否准确。

---

### 2. Pricing Gap（定价差距）

**定义**：定价时假设的违约率与实际违约率之间的差距。

**计算公式**：`implied_default_rate - actual_default_rate`

**涉及的表和字段**：
- `risk_grade.implied_default_rate`：定价假设
- 计算出的 `actual_default_rate`：实际表现

**简化 SQL**：

```sql
SELECT
    rg.grade_code,
    rg.implied_default_rate AS 定价假设,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS 实际违约率,
    ROUND(rg.implied_default_rate - 100.0 * COUNT(de.id) / COUNT(l.id), 2) AS 定价差距
FROM risk_grade rg
JOIN loan l ON rg.id = l.risk_grade_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY rg.id, rg.grade_code, rg.implied_default_rate;
```

**业务意义**：
- **正值**：定价偏高（收费过多），客户可能流失
- **负值**：定价偏低（收费不足），公司亏损
- C 级贷款的定价差距约为 -5%，说明严重定价不足

---

### 3. Approval Rate（审批通过率）

**定义**：提交的申请中被批准的比例。

**计算公式**：`批准数 / 总申请数 × 100%`

**涉及的表和字段**：
- `application.status_id`
- `loan_status.status_code = 'APPROVED'`

**简化 SQL**：

```sql
SELECT
    COUNT(*) AS 总申请数,
    COUNT(CASE WHEN ls.status_code = 'APPROVED' THEN 1 END) AS 批准数,
    ROUND(100.0 * COUNT(CASE WHEN ls.status_code = 'APPROVED' THEN 1 END) / COUNT(*), 2) AS 审批通过率
FROM application a
JOIN loan_status ls ON a.status_id = ls.id;
```

**业务意义**：监控审批松紧度，过高可能导致违约增加，过低可能损失收入。

---

### 4. False Rejection / Approval Leakage（误拒/审批漏失）

**定义**：被拒绝但实际上符合「成功借款人画像」的申请。

**判断标准**：被拒客户的 credit_score、annual_revenue、employee_count 接近或超过成功借款人的平均值。

**涉及的表和字段**：
- `application`（status = REJECTED）
- `customer`（credit_score, annual_revenue, employee_count）
- 对比成功借款人的特征

**简化 SQL**：

```sql
-- 先计算成功借款人的平均画像
WITH successful_profile AS (
    SELECT
        AVG(c.credit_score) AS avg_score,
        AVG(c.annual_revenue) AS avg_revenue
    FROM loan l
    JOIN customer c ON l.customer_id = c.id
    JOIN loan_status ls ON l.current_status_id = ls.id
    WHERE ls.status_code IN ('CURRENT', 'PAID_OFF')  -- 表现良好的贷款
)
-- 找出被拒但画像优秀的申请
SELECT
    a.application_number,
    c.credit_score,
    a.rejection_reason
FROM application a
JOIN customer c ON a.customer_id = c.id
JOIN loan_status ls ON a.status_id = ls.id
CROSS JOIN successful_profile sp
WHERE ls.status_code = 'REJECTED'
  AND c.credit_score >= sp.avg_score - 30;  -- 信用分接近成功借款人
```

**业务意义**：每个误拒代表潜在的利息收入损失，约 23% 的拒绝可能是「误拒」。

---

### 5. Late Payment Rate（逾期率）

**定义**：所有还款中逾期的比例。

**计算公式**：`逾期还款数 / 总还款数 × 100%`

**涉及的表和字段**：
- `payment.days_late`（> 0 表示逾期）

**简化 SQL**：

```sql
SELECT
    COUNT(*) AS 总还款数,
    COUNT(CASE WHEN days_late > 0 THEN 1 END) AS 逾期数,
    ROUND(100.0 * COUNT(CASE WHEN days_late > 0 THEN 1 END) / COUNT(*), 2) AS 逾期率,
    ROUND(AVG(CASE WHEN days_late > 0 THEN days_late END), 1) AS 平均逾期天数
FROM payment;
```

**业务意义**：逾期率上升是组合恶化的早期信号，通常领先违约 6-12 个月。

---

### 6. Partial Payment（部分还款）

**定义**：客户支付金额低于应还金额的情况。

**判断标准**：`payment_amount < monthly_payment × 95%`（允许 5% 误差）

**涉及的表和字段**：
- `payment.payment_amount`
- `loan.monthly_payment`

**简化 SQL**：

```sql
SELECT
    p.loan_id,
    p.installment_number,
    p.payment_amount AS 实付,
    l.monthly_payment AS 应付,
    ROUND(100.0 * p.payment_amount / l.monthly_payment, 1) AS 支付比例
FROM payment p
JOIN loan l ON p.loan_id = l.id
WHERE p.payment_amount < l.monthly_payment * 0.95;
```

**业务意义**：部分还款是资金紧张的信号，结合逾期模式可预测违约。

---

### 7. Recovery Rate（回收率）

**定义**：违约后通过催收、资产处置等方式回收的金额占违约敞口的比例。

**计算公式**：`recovery_amount / outstanding_at_default × 100%`

**涉及的表和字段**：
- `default_event.recovery_amount`
- `default_event.outstanding_at_default`

**简化 SQL**：

```sql
SELECT
    SUM(recovery_amount) AS 总回收,
    SUM(outstanding_at_default) AS 总敞口,
    ROUND(100.0 * SUM(recovery_amount) / SUM(outstanding_at_default), 2) AS 回收率
FROM default_event;
```

**业务意义**：回收率影响拨备计算，A 级贷款回收率约 40-50%，E 级仅 20-30%。

---

### 8. Loss Severity（损失严重程度）

**定义**：违约后的净损失占违约敞口的比例。

**计算公式**：`loss_amount / outstanding_at_default × 100%`（或 `1 - Recovery Rate`）

**涉及的表和字段**：
- `default_event.loss_amount`
- `default_event.outstanding_at_default`

**简化 SQL**：

```sql
SELECT
    rg.grade_code,
    ROUND(100.0 * SUM(de.loss_amount) / SUM(de.outstanding_at_default), 2) AS 损失严重程度
FROM default_event de
JOIN loan l ON de.loan_id = l.id
JOIN risk_grade rg ON l.risk_grade_id = rg.id
GROUP BY rg.grade_code;
```

**业务意义**：用于计算预期损失 = 违约概率 × 损失严重程度 × 敞口。

---

### 9. Expected Loss（预期损失）

**定义**：基于风险等级估算的潜在损失金额。

**计算公式**：`outstanding_balance × implied_default_rate / 100`

**涉及的表和字段**：
- `loan.outstanding_balance`
- `risk_grade.implied_default_rate`

**简化 SQL**：

```sql
SELECT
    l.loan_number,
    l.outstanding_balance,
    rg.implied_default_rate,
    ROUND(l.outstanding_balance * rg.implied_default_rate / 100, 2) AS 预期损失
FROM loan l
JOIN risk_grade rg ON l.risk_grade_id = rg.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE ls.status_code = 'CURRENT'
ORDER BY 预期损失 DESC
LIMIT 10;
```

**业务意义**：用于识别高风险敞口，优先关注预期损失最大的贷款。

---

### 10. Portfolio Concentration（投资组合集中度）

**定义**：某个行业在整体贷款组合中的占比。

**计算公式**：`行业敞口 / 总敞口 × 100%`

**涉及的表和字段**：
- `loan.outstanding_balance`
- `customer.industry_id`
- `industry.industry_name`

**简化 SQL**：

```sql
SELECT
    i.industry_name,
    SUM(l.outstanding_balance) AS 行业敞口,
    ROUND(100.0 * SUM(l.outstanding_balance) /
          (SELECT SUM(outstanding_balance) FROM loan), 2) AS 占比
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN industry i ON c.industry_id = i.id
GROUP BY i.industry_name
ORDER BY 占比 DESC;
```

**业务意义**：单一行业占比过高会带来系统性风险，餐饮业占比约 28%，需要设置上限。

---

### 11. Days to Decision（审批周期）

**定义**：从申请提交到做出决定的天数。

**计算公式**：`decision_date - application_date`

**涉及的表和字段**：
- `application.application_date`
- `application.decision_date`

**简化 SQL**：

```sql
SELECT
    lo.first_name || ' ' || lo.last_name AS 信贷专员,
    COUNT(a.id) AS 处理申请数,
    ROUND(AVG(JULIANDAY(a.decision_date) - JULIANDAY(a.application_date)), 1) AS 平均审批天数,
    ROUND(100.0 * COUNT(CASE WHEN JULIANDAY(a.decision_date) - JULIANDAY(a.application_date) <= 7 THEN 1 END)
          / COUNT(a.id), 1) AS SLA达标率
FROM application a
JOIN loan_officer lo ON a.loan_officer_id = lo.id
WHERE a.decision_date IS NOT NULL
GROUP BY lo.id;
```

**业务意义**：SLA 目标通常是 7 天内决定，超时会影响客户体验和转化率。

---

### 12. Payment Behavior Cohort（还款行为队列）

**定义**：根据前 6 个月的还款行为将贷款分组，分析各组的违约率。

**分组标准**：
- Perfect（完美）：从不逾期、从不部分还款
- Mostly On-Time（基本准时）：最多 1 次逾期
- Problematic（问题）：2+ 次逾期或有部分还款

**涉及的表和字段**：
- `payment`（前 6 期的 days_late, payment_amount）
- `loan.monthly_payment`
- `default_event`

**简化 SQL**：

```sql
WITH early_behavior AS (
    SELECT
        p.loan_id,
        SUM(CASE WHEN p.days_late > 0 THEN 1 ELSE 0 END) AS 逾期次数,
        SUM(CASE WHEN p.payment_amount < l.monthly_payment * 0.95 THEN 1 ELSE 0 END) AS 部分还款次数
    FROM payment p
    JOIN loan l ON p.loan_id = l.id
    WHERE p.installment_number <= 6
    GROUP BY p.loan_id
),
cohort AS (
    SELECT
        loan_id,
        CASE
            WHEN 逾期次数 = 0 AND 部分还款次数 = 0 THEN 'Perfect'
            WHEN 逾期次数 <= 1 AND 部分还款次数 = 0 THEN 'Mostly On-Time'
            ELSE 'Problematic'
        END AS 队列
    FROM early_behavior
)
SELECT
    c.队列,
    COUNT(DISTINCT l.id) AS 贷款数,
    COUNT(de.id) AS 违约数,
    ROUND(100.0 * COUNT(de.id) / COUNT(DISTINCT l.id), 2) AS 违约率
FROM cohort c
JOIN loan l ON c.loan_id = l.id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY c.队列;
```

**业务意义**：Problematic 队列违约率可达 15-25%，Perfect 队列仅 2-4%，可用于早期干预。

---

### 13. Customer Lifetime Value (LTV)（客户终身价值）

**定义**：客户在整个关系周期内为公司带来的总价值。

**计算公式**：`总借款额 + 预估利息收入 - (违约数 × 平均损失)`

**涉及的表和字段**：
- `customer.is_repeat_customer`
- `loan.approved_amount`, `interest_rate`, `term_months`
- `default_event`

**简化 SQL**：

```sql
SELECT
    CASE WHEN c.is_repeat_customer = 1 THEN '回头客' ELSE '新客户' END AS 客户类型,
    COUNT(DISTINCT c.id) AS 客户数,
    COUNT(l.id) AS 贷款数,
    ROUND(AVG(l.approved_amount), 0) AS 平均贷款额,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS 违约率
FROM customer c
LEFT JOIN loan l ON c.id = l.customer_id
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY c.is_repeat_customer;
```

**业务意义**：回头客违约率约 3.2%，新客户约 9.1%，应优先投资客户留存。

---

### 14. Vintage Analysis（年份分析）

**定义**：按贷款发放时间（季度/月份）分组，追踪各批次的表现。

**涉及的表和字段**：
- `loan.disbursement_date`
- `default_event`

**简化 SQL**：

```sql
SELECT
    strftime('%Y-Q' || ((CAST(strftime('%m', l.disbursement_date) AS INTEGER) - 1) / 3 + 1),
             l.disbursement_date) AS 季度,
    COUNT(l.id) AS 发放数,
    COUNT(de.id) AS 违约数,
    ROUND(100.0 * COUNT(de.id) / COUNT(l.id), 2) AS 违约率
FROM loan l
LEFT JOIN default_event de ON l.id = de.loan_id
GROUP BY 季度
ORDER BY 季度;
```

**业务意义**：如果新季度违约率高于历史同期，说明审批标准可能放松了。

---

### 15. Risk Grade Migration（风险等级迁移）

**定义**：客户信用分提升后，可能有资格获得更优惠的利率（迁移到更好的风险等级）。

**判断标准**：`当前信用分 > 原风险等级的 max_credit_score`

**涉及的表和字段**：
- `customer.credit_score`
- `loan.risk_grade_id`
- `risk_grade.max_credit_score`, `interest_rate`

**简化 SQL**：

```sql
SELECT
    l.loan_number,
    c.credit_score AS 当前信用分,
    rg_current.grade_code AS 贷款等级,
    rg_current.max_credit_score AS 等级上限,
    rg_current.interest_rate AS 当前利率,
    l.outstanding_balance,
    -- 找到客户现在应该属于的等级
    (SELECT rg2.grade_code FROM risk_grade rg2
     WHERE c.credit_score BETWEEN rg2.min_credit_score AND rg2.max_credit_score) AS 应属等级
FROM loan l
JOIN customer c ON l.customer_id = c.id
JOIN risk_grade rg_current ON l.risk_grade_id = rg_current.id
JOIN loan_status ls ON l.current_status_id = ls.id
WHERE ls.status_code = 'CURRENT'
  AND c.credit_score > rg_current.max_credit_score + 10  -- 信用分已超过当前等级
ORDER BY l.outstanding_balance DESC
LIMIT 10;
```

**业务意义**：主动联系这些客户提供再融资，可提升客户满意度和留存率。

---

## 概念之间的关系

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

这些概念共同构成了贷款风险管理的分析框架：
1. **事前**：Expected Loss、Portfolio Concentration 用于控制风险敞口
2. **事中**：Late Payment Rate、Payment Behavior Cohort 用于监控预警
3. **事后**：Recovery Rate、Loss Severity 用于评估实际损失

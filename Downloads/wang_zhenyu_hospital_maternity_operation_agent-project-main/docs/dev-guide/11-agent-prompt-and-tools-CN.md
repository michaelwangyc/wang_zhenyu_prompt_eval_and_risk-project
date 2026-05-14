# Agent 核心：Prompt 与 Tool

本文档介绍 AI Agent 最重要的两个部分：**System Prompt**（系统提示词）和 **Tool**（工具）。

---

## Strands Agents 框架

### Agent 与普通聊天 AI 的区别

普通聊天 AI 只能对话，无法访问外部系统。用户问「今天病房有几个病人」，它只能猜测或回答不知道。

**Agent** 则被赋予了「工具」，可以实际执行操作：

| 对比 | 普通聊天 AI | Agent |
|------|-------------|-------|
| 能做什么 | 只能聊天 | 能聊天 + 能执行操作 |
| 问「病房有几个病人」 | 猜测或说不知道 | 查询数据库，返回准确数字 |
| 问「帮我分配床位」 | 给建议，但不执行 | 实际修改数据库 |

### Strands 框架结构

**Strands** 是一个 Python 库，用于构建 Agent。创建一个 Agent 需要三个要素：

```python
from strands import Agent, tool

agent = Agent(
    model=bedrock_model,           # AI 模型（如 Claude）
    system_prompt="你是一个...",    # 系统提示词（行为规则）
    tools=[tool1, tool2, tool3],   # 工具列表（可调用的函数）
)
```

- `model`：AI 的模型，决定推理能力
- `system_prompt`：告诉 AI 它的角色和行为规则
- `tools`：AI 可以调用的工具列表

---

## Tool 定义

### Tool 的本质

**Tool** 是一个被 `@tool` 装饰器标记的函数。装饰器告诉框架：「这个函数可以被 AI 调用」。

### 工作流程

当用户问「病房有几个病人」时：

```
用户提问 → AI 分析问题 → 决定调用工具 → 执行工具 → 获得结果 → 组织回答
```

AI 会阅读工具的 docstring 来理解：这个工具做什么、需要什么参数、返回什么结果。

### Tool 定义示例

**文件位置：** `labor_ward_ai/one/one_04_agent.py`

```python
from strands import tool

@tool(name="execute_sql_query")
def tool_execute_sql_query(self, sql: str) -> str:
    """
    Execute a SQL SELECT query and return results as a Markdown table.

    Args:
        sql: A valid SQL SELECT query string to execute.

    Returns:
        A Markdown-formatted table with query results.
    """
    return self.execute_and_print_result(sql=sql)
```

**各部分说明：**

| 代码 | 作用 |
|------|------|
| `@tool(name="execute_sql_query")` | 注册为工具，AI 用这个名字调用 |
| `sql: str` | 参数类型提示，AI 知道应传字符串 |
| `-> str` | 返回类型，告诉框架返回值是字符串 |
| docstring | AI 阅读这段文字来理解工具用途 |

**重要：** docstring 写得清晰与否直接影响 AI 能否正确使用工具。

---

## 纯函数与 Tool 封装的分离

### 代码组织

```
labor_ward_ai/
├── write_operations.py     # 纯函数：assign_bed(), create_order() 等
│
└── one/
    └── one_04_agent.py     # Tool 封装：tool_assign_bed(), tool_create_order() 等
```

### 为什么分开？

**纯函数：**
```python
# write_operations.py
def assign_bed(engine, admission_id: str, bed_id: str) -> dict:
    """分配床位的核心逻辑"""
    # ... 数据库操作 ...
    return {"success": True, "message": "..."}
```

**Tool 封装：**
```python
# one_04_agent.py
@tool(name="assign_bed")
def tool_assign_bed(self, admission_id: str, bed_id: str) -> str:
    """
    Assign or transfer a patient to a bed.

    Use this tool when:
    - A new patient needs to be assigned to an available bed
    - A patient needs to be transferred to a different bed
    [...]
    """
    result = write_operations.assign_bed(
        engine=self.engine,
        admission_id=admission_id,
        bed_id=bed_id,
    )
    return json.dumps(result)
```

### 分离的好处

| 对比 | 测试纯函数 | 测试 Tool |
|------|-----------|----------|
| 方式 | 直接调用，传参数 | 启动 AI，用自然语言提问 |
| 速度 | 毫秒级 | 秒级（等待 API 响应） |
| 成本 | 免费 | 消耗 API 费用 |
| 可预测性 | 100% 确定 | AI 可能理解错误 |

**设计原则：**
1. 核心业务逻辑写成纯函数（方便测试、复用）
2. Tool 只做薄封装：加 `@tool` 标签、写 docstring、调用纯函数、格式化返回值

---

## System Prompt 详解

### 什么是 System Prompt

**System Prompt** 是给 AI 的「工作手册」，定义它的角色、能力、行为规则。

**文件位置：** `labor_ward_ai/prompts/bi-agent-system-prompt.md`

### Prompt 的关键组成部分

#### 1. 角色定义

```markdown
You are MaterniFlow BI Agent, an intelligent database assistant for OB/GYN ward operations.
```

告诉 AI 它的身份，影响回答的风格和专业性。

#### 2. 工具说明

```markdown
## Available Tools

1. **get_database_schema** - Call this FIRST to understand the database structure
2. **execute_sql_query** - Execute SQL SELECT queries against the database
3. **assign_bed** - Assign or transfer a patient to a bed
...
```

虽然 `@tool` 已经注册了工具，但在 Prompt 里再次说明可以告诉 AI **什么时候该用**、**使用顺序**、**使用场景**。

#### 3. 工作流程

```markdown
## Workflow

1. When receiving a question, first call `get_database_schema` if you haven't already
2. Analyze the schema to identify relevant tables and columns
3. Write an appropriate SQL query
4. Call `execute_sql_query` to get results
5. Interpret the results and provide a helpful answer
```

明确的步骤减少 AI 漏步骤或乱序执行。

#### 4. 数据库知识

```markdown
## Database Overview

The database contains 11 tables for managing an OB/GYN ward:

| Table | Purpose |
|-------|---------|
| patient | Basic patient identity information |
| admission | Patient admission records |
...
```

预先告诉 AI 业务背景，不用每次都从头查询。

#### 5. 查询规范

```markdown
## Query Guidelines

- Limit to a maximum of **20 rows**
- Use `occupied * 1.0 / total * 100` for percentages (SQLite integer division fix)
```

常见陷阱的预防措施，例如 SQLite 整数除法问题。

#### 6. 响应风格

```markdown
## Response Style

- Be concise and professional
- Lead with the direct answer, then provide supporting details
- Highlight critical information (high-risk patients, urgent items)
```

规定 AI 的回答风格，适合医疗场景的简洁专业风格。

#### 7. 示例对话

```markdown
## Example Interactions

**User**: "Assign patient Wang to triage bed 01"

**Agent**:
1. Query to find Wang's admission_id
2. Query to find triage-01 bed_id
3. Call `assign_bed(admission_id="...", bed_id="...")`
4. Response: "Done. Patient Wang has been assigned to triage bed 01."
```

示例是最有效的教学方式，AI 会模仿这些模式。

#### 8. 安全规则

```markdown
## Safety Notes

- **Always query first** before executing write operations
- Never execute raw UPDATE, INSERT, DELETE, or DROP SQL statements
- Only use the provided write operation tools
```

安全底线，禁止 AI 执行危险操作。

### Prompt 各部分的作用总结

| 部分 | 解决的问题 |
|------|-----------|
| 角色定义 | 确定 AI 的「人设」和专业领域 |
| 工具说明 | 告诉 AI 何时使用哪个工具 |
| 工作流程 | 提供标准操作流程 |
| 数据库知识 | 预先科普业务背景 |
| 查询规范 | 避免常见错误 |
| 响应风格 | 规定回答的语气和格式 |
| 示例对话 | 提供可模仿的模式 |
| 安全规则 | 划定不可逾越的底线 |

---

## 项目中的 Tool 列表

### 只读工具

| 工具名 | 功能 | 用途 |
|--------|------|------|
| `get_database_schema` | 获取数据库表结构 | AI 在写 SQL 前先了解表结构 |
| `execute_sql_query` | 执行 SQL 查询 | 查询数据，返回 Markdown 表格 |
| `write_debug_report` | 写调试报告 | 记录 AI 思考过程，便于排查 |

### 写入工具

| 工具名 | 功能 | 对应纯函数 |
|--------|------|-----------|
| `assign_bed` | 分配床位 | `write_operations.assign_bed()` |
| `update_prediction` | 更新出院预测 | `write_operations.update_prediction()` |
| `create_alert` | 创建高危警报 | `write_operations.create_alert()` |
| `create_order` | 创建医嘱 | `write_operations.create_order()` |

每个写入工具都有对应的纯函数，Tool 只是薄封装。

---

## 相关文件

| 文件 | 内容 |
|------|------|
| `labor_ward_ai/one/one_04_agent.py` | Tool 定义和 Agent 创建 |
| `labor_ward_ai/prompts/bi-agent-system-prompt.md` | System Prompt |
| `labor_ward_ai/write_operations.py` | 写操作纯函数 |
| `data/database-exploration/database-schema.txt` | 数据库结构参考 |

---

## 添加新工具的步骤

1. 如果需要写数据库，在 `write_operations.py` 添加纯函数
2. 在 `one_04_agent.py` 添加 `@tool` 方法
3. 在 Agent 的 `tools=[]` 列表中注册
4. 在 System Prompt 中添加工具说明

---

## 设计原则

本项目采用「纯函数 + Tool 封装」模式，体现了**分离关注点**原则：

- **纯函数**：关注「怎么做事」（业务逻辑），易于测试和复用
- **Tool 封装**：关注「怎么让 AI 调用」（接口适配），专注于 AI 交互

# 本地测试 Agent

本文档介绍如何在本地测试 AI Agent，确保它按预期工作后再部署到 UI 应用。

读完这篇文档，你会明白：
- 为什么要在本地测试 Agent
- 如何使用 `agent_debugger.py` 调试助手
- 如何运行单轮和多轮对话测试
- 如何读懂测试输出

---

## 为什么要本地测试？

### 先想一个问题

**思考一下：** 如果你写好了 Agent 代码，想测试一下它能不能正确回答问题，你会怎么做？

给自己 10 秒想一想...

---

很多新手的第一反应是：「启动 Web 应用，在聊天界面里试一下！」

这样做**可以**，但**效率很低**：

| 对比 | 在 UI 上测试 | 在终端本地测试 |
|------|-------------|---------------|
| 启动时间 | 等 Next.js + FastAPI 启动 | 直接跑 Python 脚本 |
| 看输出 | 只能看最终回答 | 能看 Agent 的思考过程 |
| 调试 | 出错了不知道哪里错 | 能看到每一步的输入输出 |
| 重复测试 | 每次都要手动输入 | 一条命令重跑 |
| 适合阶段 | 最终验收、演示 | 开发、调试、快速迭代 |

**类比理解：**

想象你在做菜。你不会每炒完一道菜就端给客人尝吧？肯定是先自己尝一口，确认味道对了，再上桌。

本地测试就是「自己先尝一口」。确认 Agent 工作正常了，再让用户在 UI 上使用。

---

## 测试脚本一览

在 `scripts/` 目录下有 5 个测试脚本：

| 脚本 | 用途 | 测试类型 |
|------|------|----------|
| `test_agent.py` | 测试单轮查询能力 | 10 个预定义问题，从简单到复杂 |
| `test_agent_1_assign_bed.py` | 测试床位分配功能 | 3 轮对话：查询 → 执行 → 验证 |
| `test_agent_2_update_prediction.py` | 测试更新出院预测 | 3 轮对话：查询 → 执行 → 验证 |
| `test_agent_3_create_order.py` | 测试创建医嘱 | 3 轮对话：查询 → 执行 → 验证 |
| `test_agent_4_create_alert.py` | 测试创建高危警报 | 3 轮对话：查询 → 执行 → 验证 |

**设计思路：**

- `test_agent.py`：测试 Agent 的**只读查询**能力（读数据库、生成 SQL）
- `test_agent_1~4.py`：测试 Agent 的**写入操作**能力（调用 Tool 修改数据库）

---

## agent_debugger 调试助手

### 这是什么？

`labor_ward_ai/agent_debugger.py` 是一个调试工具模块，帮你：

1. **格式化输出** — 把 Agent 的响应整理成易读的格式
2. **分离思考与回答** — 把 `<thinking>` 标签里的思考过程和最终回答分开显示
3. **支持多轮对话** — 跟踪每一轮对话的输入输出

### 核心函数

| 函数 | 作用 | 什么时候用 |
|------|------|-----------|
| `chat()` | 发送消息给 Agent，返回思考过程和最终回答 | 每次和 Agent 对话 |
| `print_summary()` | 打印多轮对话的摘要 | 测试结束后查看总结 |
| `extract_text_from_messages()` | 从 Agent 消息中提取文本 | 底层函数，通常不直接调用 |
| `parse_response_text()` | 把完整响应解析成思考+回答 | 底层函数，通常不直接调用 |

### chat() 函数详解

这是你最常用的函数：

```python
from labor_ward_ai.agent_debugger import chat

# 发送消息给 Agent
thinking, answer = chat(
    agent,           # Agent 实例
    "你的问题",       # 用户消息
    turn_number=1,   # 第几轮对话（用于显示）
    verbose=False,   # 是否显示原始流式输出
    debug=False,     # 是否显示消息结构调试信息
)
```

**返回值：**
- `thinking`：Agent 的思考过程（`<thinking>` 标签内的内容）
- `answer`：Agent 的最终回答

**输出格式：**

运行时会自动打印：

```
======================================================================
  TURN 1
======================================================================

[REQUEST]
----------------------------------------------------------------------
你的问题

[THINKING]
----------------------------------------------------------------------
Agent 的思考过程...

[RESPONSE]
----------------------------------------------------------------------
Agent 的最终回答...
```

---

## test_agent.py — 单轮查询测试

### 文件位置

```
scripts/test_agent.py
```

### 预定义的 10 个测试问题

脚本里定义了从简单到复杂的 10 个问题：

**入门级（1-3）：理解系统**

| 编号 | 问题 | 测试什么 |
|------|------|----------|
| request_01 | "What can you help me with?" | Agent 能否介绍自己的能力 |
| request_02 | "Explain the main entities in this database" | Agent 能否解释数据库结构 |
| request_03 | "What does the admission workflow look like?" | Agent 能否解释业务流程 |

**简单查询（4-6）：基础 SQL**

| 编号 | 问题 | 测试什么 |
|------|------|----------|
| request_04 | "How many patients are currently in the ward?" | 简单 COUNT 查询 |
| request_05 | "Which beds are currently available?" | 带条件的 SELECT 查询 |
| request_06 | "Show me today's scheduled procedures" | 日期过滤查询 |

**中等复杂（7-8）：JOIN 和聚合**

| 编号 | 问题 | 测试什么 |
|------|------|----------|
| request_07 | "Who are the high-risk patients?" | 多表 JOIN 查询 |
| request_08 | "What's the bed occupancy rate?" | 聚合 + 分组 + 百分比计算 |

**高级复杂（9-10）：多步推理**

| 编号 | 问题 | 测试什么 |
|------|------|----------|
| request_09 | "For patients in labor, show labor progress" | 多表 JOIN + 时间计算 |
| request_10 | "Give me a shift handover summary" | 需要执行多个 SQL 查询的综合报告 |

### 如何运行

**步骤 1：打开脚本，选择要测试的问题**

```python
# 在文件末尾找到这一行，改成你想测试的问题编号
request = request_04  # 改成 request_01 到 request_10 中的任意一个
```

**步骤 2：运行脚本**

```bash
.venv/bin/python scripts/test_agent.py
```

**步骤 3：观察输出**

Agent 会打印它的思考过程和最终回答。如果你启用了 `write_debug_report` 工具，还会生成 `tmp/debug_report.md` 文件。

### 输出示例

```
我将首先获取数据库架构，然后执行查询以获取当前病房中的患者数量...

<thinking>
用户想知道病房里有多少病人，我需要：
1. 先查看数据库结构
2. 找到存储病人信息的表
3. 写 SQL 查询统计数量
</thinking>

根据查询结果，目前病房共有 15 位患者，按入院状态分布如下：

| 状态 | 人数 |
|------|------|
| admitted | 4 |
| in_labor | 5 |
| postpartum | 4 |
| ready_for_discharge | 2 |
```

---

## test_agent_1~4.py — 多轮写入测试

### 设计模式：查询 → 执行 → 验证

这 4 个脚本都遵循相同的 3 轮对话模式：

```
Turn 1: 查询 (Query)
    ↓
    用户问「我要做 X 操作，先帮我找一下相关数据」
    Agent 执行 SQL 查询，返回需要的信息
    ↓
Turn 2: 执行 (Execute)
    ↓
    用户说「好的，现在执行操作」
    Agent 调用写入工具（如 assign_bed）
    ↓
Turn 3: 验证 (Verify)
    ↓
    用户说「验证一下操作是否成功」
    Agent 再次查询数据库，确认数据已更新
```

**为什么要这样设计？**

这模拟了真实的护士工作流程：
1. 先了解情况（查询）
2. 做出决定并执行（调用工具）
3. 确认执行成功（验证）

### test_agent_1_assign_bed.py 详解

以床位分配测试为例，看看代码是怎么写的：

```python
from labor_ward_ai.one.api import one
from labor_ward_ai.tests.db_sync import reset_remote_database
from labor_ward_ai.agent_debugger import chat, print_summary

def test_assign_bed_full(debug: bool = False):
    # 获取 Agent 实例，清空历史消息
    agent = one.agent
    agent.messages.clear()

    results = []

    # Turn 1: 查询 — 找一个有床位的病人和一个空床位
    request_01 = """
I need to transfer a patient to a different bed. Please find:
1. A patient who currently HAS a bed assigned
2. An available bed in postpartum area
""".strip()

    thinking, answer = chat(agent, request_01, turn_number=1, debug=debug)
    results.append(("Query", thinking, answer))

    # Turn 2: 执行 — 调用 assign_bed 工具
    request_02 = """
Good. Now transfer the first patient to the first available postpartum bed.
Use the assign_bed tool.
""".strip()

    thinking, answer = chat(agent, request_02, turn_number=2)
    results.append(("Execute", thinking, answer))

    # Turn 3: 验证 — 确认转床成功
    request_03 = """
Verify the transfer was successful. Check:
1. The patient's new bed assignment
2. The old bed is now available
3. The new bed is now occupied
""".strip()

    thinking, answer = chat(agent, request_03, turn_number=3)
    results.append(("Verify", thinking, answer))

    return results

if __name__ == "__main__":
    reset_remote_database(verbose=False)  # 重置数据库到初始状态
    results = test_assign_bed_full()
    print_summary(results)
```

**关键点解释：**

**第 1 行：** `agent.messages.clear()`
- 清空 Agent 的对话历史
- 确保每次测试都是从头开始

**第 2 行：** `reset_remote_database()`
- 重置数据库到初始状态
- 确保每次测试的数据环境一致

**第 3 行：** `results.append(("Query", thinking, answer))`
- 收集每轮对话的结果
- 最后用 `print_summary()` 打印摘要

### 如何运行

```bash
# 测试床位分配
.venv/bin/python scripts/test_agent_1_assign_bed.py

# 测试更新出院预测
.venv/bin/python scripts/test_agent_2_update_prediction.py

# 测试创建医嘱
.venv/bin/python scripts/test_agent_3_create_order.py

# 测试创建警报
.venv/bin/python scripts/test_agent_4_create_alert.py
```

### 输出示例

```
======================================================================
  TEST: assign_bed - Multi-turn conversation (3 turns)
======================================================================

======================================================================
  TURN 1
======================================================================

[REQUEST]
----------------------------------------------------------------------
I need to transfer a patient to a different bed...

[THINKING]
----------------------------------------------------------------------
用户需要转床，我需要先找到一个有床位的病人和一个空的产后区床位...

[RESPONSE]
----------------------------------------------------------------------
I found the following information:

**Patients with beds:**
| admission_id | patient_name | bed_label | room_number |
|...

**Available postpartum beds:**
| bed_id | bed_label | room_number |
|...

======================================================================
  TURN 2
======================================================================

[REQUEST]
----------------------------------------------------------------------
Good. Now transfer the first patient to the first available postpartum bed...

[THINKING]
----------------------------------------------------------------------
用户确认要转床，我需要调用 assign_bed 工具...

[RESPONSE]
----------------------------------------------------------------------
Done! Patient has been transferred to bed P-201-A.

======================================================================
  TURN 3
======================================================================

[REQUEST]
----------------------------------------------------------------------
Verify the transfer was successful...

[RESPONSE]
----------------------------------------------------------------------
Transfer verified successfully:
- Patient is now in bed P-201-A
- Old bed is now available
- New bed is now occupied

======================================================================
  SUMMARY
======================================================================

[Query]
  Thinking: 245 chars
  Answer: 512 chars

[Execute]
  Thinking: 128 chars
  Answer: 89 chars

[Verify]
  Thinking: 156 chars
  Answer: 234 chars
```

---

## 调试技巧

### 1. 开启 debug 模式查看消息结构

```python
thinking, answer = chat(agent, request, turn_number=1, debug=True)
```

这会打印出 Agent 消息的详细结构，帮你理解 Strands Agent 的内部工作方式。

### 2. 开启 verbose 模式查看原始输出

```python
thinking, answer = chat(agent, request, turn_number=1, verbose=True)
```

这会显示 Agent 的原始流式输出，包括 AI 正在「打字」的过程。

### 3. 检查 debug_report.md

如果 Agent 启用了 `write_debug_report` 工具，每次回答后会生成调试报告：

```bash
cat tmp/debug_report.md
```

这个文件记录了 Agent 的完整推理过程：执行了哪些 SQL、得到了什么结果、如何得出答案。

### 4. 单独测试纯函数

如果 Agent 调用 Tool 时出错，可以单独测试底层的纯函数：

```python
from labor_ward_ai.write_operations import assign_bed
from labor_ward_ai.one.api import one

# 直接调用纯函数，跳过 Agent
result = assign_bed(
    engine=one.engine,
    admission_id="xxx",
    bed_id="yyy",
)
print(result)
```

这样可以快速定位问题是出在 Agent 层还是业务逻辑层。

---

## 测试流程建议

### 新手推荐流程

```
1. 先跑 test_agent.py 的简单问题 (request_01 ~ request_03)
   ↓
   确认 Agent 能正常启动、能回答问题

2. 跑中等复杂度问题 (request_04 ~ request_08)
   ↓
   确认 Agent 能正确生成 SQL、查询数据库

3. 跑复杂问题 (request_09 ~ request_10)
   ↓
   确认 Agent 能处理多步推理

4. 跑多轮对话测试 (test_agent_1~4.py)
   ↓
   确认 Agent 能正确调用写入工具

5. 在 UI 上做最终验收
   ↓
   确认整体流程正常
```

### 修改代码后的测试流程

```
1. 改了 System Prompt？
   → 跑 test_agent.py 看回答风格是否符合预期

2. 改了 Tool 定义？
   → 跑对应的 test_agent_X.py 验证功能

3. 改了纯函数？
   → 先跑 pytest 测试纯函数
   → 再跑 test_agent_X.py 测试 Agent 调用
```

---

## 常见问题

### Q: 测试时报错 "Database connection error"

**原因：** 数据库连接信息不对，或数据库不可用。

**解决：**
1. 检查 `.env` 文件中的数据库配置
2. 确认数据库服务正在运行
3. 如果用本地 SQLite，确认 `tmp/data.sqlite` 文件存在

### Q: Agent 回答不稳定，每次结果不一样

**原因：** AI 本身就有一定的随机性，这是正常的。

**解决：**
1. 检查 System Prompt 是否足够明确
2. 在提问时给出更具体的指令
3. 多跑几次，确认「大方向」是对的即可

### Q: Tool 调用失败

**原因：** 可能是参数格式不对，或 Tool 的 docstring 不够清晰。

**解决：**
1. 检查 Tool 的 docstring 是否清楚说明了参数格式
2. 在提问时明确告诉 Agent 参数值
3. 开启 `debug=True` 查看消息结构

---

## 总结

| 要点 | 说明 |
|------|------|
| **本地测试优先** | 在终端测试完再去 UI 验收 |
| **test_agent.py** | 测试单轮查询，10 个从简单到复杂的问题 |
| **test_agent_1~4.py** | 测试多轮对话 + 写入操作 |
| **agent_debugger.py** | 调试助手，分离思考和回答 |
| **chat() 函数** | 核心函数，返回 (thinking, answer) |
| **debug/verbose 参数** | 开启更详细的调试输出 |

**记住：本地测试有信心了，才向后推进！**

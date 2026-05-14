# 前端与 Agent 集成

本文档介绍前端 UI 如何与后端 AI Agent 通信，实现聊天界面与智能助手的交互。

读完这篇文档，你会明白：
- 前端如何发送消息给后端
- 后端如何调用 Agent 并返回结果
- 如何分离显示 Agent 的「思考过程」和「最终回答」
- 什么是 SSE（Server-Sent Events）以及为什么要用它

---

## 整体架构

```
+-------------------+     HTTP POST      +-------------------+
|   Frontend (UI)   |  --------------->  |   Backend (API)   |
|   Next.js +       |                    |   FastAPI +       |
|   Vercel AI SDK   |  <---------------  |   Strands Agent   |
+-------------------+   SSE Response     +-------------------+
```

**数据流：**

1. 用户在聊天界面输入消息
2. 前端发送 HTTP POST 请求到 `/api/chat`（包含完整对话历史）
3. 后端恢复对话历史，调用 Strands Agent
4. Agent 执行工具（查询数据库、分配床位等）
5. 后端提取 Agent 的思考过程和最终回答
6. 后端通过 SSE 流式返回响应
7. 前端解析 SSE 事件，更新聊天界面

---

## 后端代码详解：api/index.py

### 文件位置

```
api/index.py
```

这是 FastAPI 后端的入口文件，定义了两个端点：
- `/api/hello` — 健康检查
- `/api/chat` — 聊天 API（核心）

### 导入的模块

```python
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
from vercel_ai_sdk_mate.api import RequestBody

from labor_ward_ai.ai_sdk_adapter import ai_sdk_message_with_reasoning_generator
from labor_ward_ai.ai_sdk_adapter import get_last_user_message_text
from labor_ward_ai.ai_sdk_adapter import request_body_to_agent_history
from labor_ward_ai.one.api import one
from labor_ward_ai.agent_debugger import extract_text_from_messages
from labor_ward_ai.agent_debugger import parse_response_text
```

**关键模块说明：**

| 模块 | 作用 |
|------|------|
| `vercel_ai_sdk_mate.api.RequestBody` | 解析 Vercel AI SDK 格式的请求 |
| `one` | 项目的单例对象，包含 Agent 实例 |
| `extract_text_from_messages` | 从 Agent 消息中提取文本 |
| `parse_response_text` | 分离思考过程和最终回答 |
| `ai_sdk_message_with_reasoning_generator` | 生成 SSE 事件流 |

### /api/chat 端点完整解析

这是核心端点，逐段分析：

#### 第一步：解析请求

```python
@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query("data")):
    # 解析请求体
    request_body_data = await debug_ai_sdk_request(request=request)
    request_body = RequestBody(**request_body_data)
```

**发生了什么：**
- 前端发送 JSON 请求，包含 `messages` 数组（完整对话历史）
- `RequestBody` 把 JSON 解析成 Python 对象

**请求格式示例：**

```json
{
  "messages": [
    { "role": "user", "parts": [{"type": "text", "text": "查询空床位"}] },
    { "role": "assistant", "parts": [{"type": "reasoning", "text": "..."}, {"type": "text", "text": "找到 3 张空床位..."}] },
    { "role": "user", "parts": [{"type": "text", "text": "把病人分配到第一张床"}] }
  ]
}
```

#### 第二步：提取最新消息

```python
    last_user_message = get_last_user_message_text(request_body)

    if not last_user_message:
        # 返回错误
        ...
```

**为什么需要这步？**

前端发送的是**完整对话历史**。最后一条消息是用户刚刚输入的，我们需要单独提取出来。

#### 第三步：恢复对话历史

```python
    agent = one.agent
    agent.messages.clear()

    history_messages = request_body_to_agent_history(request_body)
    agent.messages.extend(history_messages)
```

**这是最关键的部分！**

**问题：** 每次 HTTP 请求都是独立的。Agent 不会自动「记住」前一轮对话。

**解决方案：**
1. `agent.messages.clear()` — 清空 Agent 的消息列表
2. `request_body_to_agent_history()` — 把前端发来的历史转换成 Agent 格式
3. `agent.messages.extend()` — 恢复历史到 Agent

**`request_body_to_agent_history` 做了什么？**

```python
def request_body_to_agent_history(request_body) -> list[dict]:
    messages = []
    for message in request_body.messages[:-1]:  # 排除最后一条（当前输入）
        text_parts = []
        for part in message.parts:
            if part.type == "text":
                text_parts.append({"text": part.text})
            # 跳过 'reasoning' 类型 — Agent 不需要看到之前的思考过程
        if text_parts:
            messages.append({"role": message.role, "content": text_parts})
    return messages
```

**为什么跳过 reasoning？**

`reasoning` 是 Agent 之前的「思考过程」，是给用户看的。Agent 自己不需要看到它之前怎么「想」的 — 它只需要知道对话内容（user 说了什么，assistant 回答了什么）。

#### 第四步：调用 Agent

```python
    msg_count_before = len(agent.messages)

    # 调用 Agent（抑制标准输出）
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        agent(last_user_message)
    finally:
        sys.stdout = old_stdout
```

**发生了什么：**
- 记录调用前的消息数量（后面用于提取新消息）
- `agent(last_user_message)` — 调用 Agent，传入用户最新消息
- Agent 会思考、调用工具、生成回答

**为什么要抑制 stdout？**

Strands Agent 默认会把思考过程打印到控制台。在 API 中我们不需要这些输出，所以临时重定向到 `StringIO`。

#### 第五步：提取结果

```python
    full_text = extract_text_from_messages(agent.messages, msg_count_before)
    thinking, answer = parse_response_text(full_text)
```

**`extract_text_from_messages` 做了什么？**

从 Agent 新增的消息中提取文本。重点是：
- **Thinking**：收集**所有**消息的 `<thinking>` 内容
- **Response**：只取**最后一个**消息的非-thinking 文本

**为什么这样设计？**

Agent 可能多次「思考」和「行动」。比如：
1. 第一次思考：「我需要先查询哪些患者有床位...」
2. 调用工具：执行 SQL 查询
3. 第二次思考：「查到了 3 个患者，我再查空床位...」
4. 调用工具：执行另一个 SQL 查询
5. 最终回答：「已成功将 Julie Parker 转移到 P-201-A」

如果只取最后一个消息的 thinking，用户就看不到完整的推理过程。

**`parse_response_text` 做了什么？**

用正则表达式分离 `<thinking>...</thinking>` 标签和普通文本：

```python
def parse_response_text(full_text: str) -> tuple[str, str]:
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_matches = re.findall(thinking_pattern, full_text, re.DOTALL)
    thinking_process = "\n\n".join(match.strip() for match in thinking_matches)

    final_answer = re.sub(thinking_pattern, "", full_text, flags=re.DOTALL)
    return thinking_process, final_answer.strip()
```

#### 第六步：返回 SSE 响应

```python
    response = StreamingResponse(
        ai_sdk_message_with_reasoning_generator(
            reasoning_text=thinking,
            output_text=answer,
        ),
        media_type="text/event-stream",
    )
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    return response
```

**什么是 SSE（Server-Sent Events）？**

> SSE 是一种让服务器「主动推送」数据到浏览器的技术。
>
> 想象你在看直播。传统方式是你不停刷新页面问「有新内容吗？」（这叫 polling）。
>
> SSE 的方式是：服务器和你建立一个「通道」，有新内容时服务器直接推过来，你不用问。

**为什么用 SSE？**

聊天应用需要「边生成边发送」，而不是等 AI 全部写完再返回。SSE 让我们可以流式传输内容。

---

## SSE 事件格式：ai_sdk_adapter.py

### Vercel AI SDK v5 事件类型

| 事件类型 | 用途 |
|---------|------|
| `reasoning-start` | 开始发送思考内容 |
| `reasoning-delta` | 发送思考内容的一段 |
| `reasoning-end` | 思考内容发送完毕 |
| `text-start` | 开始发送文本内容 |
| `text-delta` | 发送文本内容的一段 |
| `text-end` | 文本内容发送完毕 |
| `finish` | 整个响应结束 |

### 生成器函数详解

```python
def ai_sdk_message_with_reasoning_generator(reasoning_text: str, output_text: str):
    # 发送 reasoning（如果有）
    if reasoning_text:
        reasoning_id = str(uuid.uuid4())
        yield f'data: {json.dumps({"type": "reasoning-start", "id": reasoning_id})}\n\n'
        yield f'data: {json.dumps({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text})}\n\n'
        yield f'data: {json.dumps({"type": "reasoning-end", "id": reasoning_id})}\n\n'

    # 发送 text
    text_id = str(uuid.uuid4())
    yield f'data: {json.dumps({"type": "text-start", "id": text_id})}\n\n'
    yield f'data: {json.dumps({"type": "text-delta", "id": text_id, "delta": output_text})}\n\n'
    yield f'data: {json.dumps({"type": "text-end", "id": text_id})}\n\n'

    yield f'data: {json.dumps({"type": "finish", "finishReason": "stop"})}\n\n'
    yield "data: [DONE]\n\n"
```

**什么是 Generator（生成器）？**

> 普通函数用 `return` 返回结果，函数就结束了。
>
> Generator 用 `yield` 返回结果，函数「暂停」在那里，下次调用继续从那里执行。
>
> 适合处理流式输出的场景。

**SSE 格式规则：**
- 每行以 `data: ` 开头
- 后面是 JSON 数据
- 以两个换行符 `\n\n` 结尾

---

## 前端关键改动

### ReasoningBlock 组件

前端需要分别显示「思考过程」和「最终回答」。我们在 `components/chat/message.tsx` 中添加了 `ReasoningBlock` 组件：

```tsx
const ReasoningBlock = ({ text }: { text: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const previewText = text.length > 100 ? text.slice(0, 100) + "..." : text;

  return (
    <div className="border border-amber-200 rounded-lg bg-amber-50">
      <button onClick={() => setIsExpanded(!isExpanded)}>
        <span>Thinking</span>
        {!isExpanded && <span>{previewText}</span>}
      </button>
      {isExpanded && (
        <div className="whitespace-pre-wrap">{text}</div>
      )}
    </div>
  );
};
```

**设计思路：**
- 默认折叠，不打扰用户
- 显示前 100 个字符作为预览
- 点击可以展开查看完整思考过程
- 淡黄色背景与普通消息区分

### 消息渲染逻辑

```tsx
{message.parts.map((part, index) => {
  if (part.type === 'reasoning' && part.text) {
    return <ReasoningBlock key={index} text={part.text} />;
  }
  if (part.type === 'text' && part.text) {
    return <Markdown>{part.text}</Markdown>;
  }
  return null;
})}
```

**Vercel AI SDK 会自动解析 SSE 事件：**
- `reasoning-delta` → `{ type: 'reasoning', text: '...' }`
- `text-delta` → `{ type: 'text', text: '...' }`

---

## 完整流程图

```
User Input: "Transfer patient to empty bed"
                    |
                    v
Frontend sends POST /api/chat
{
  "messages": [
    ...history...,
    { "role": "user", "parts": [{"type": "text", "text": "Transfer patient..."}] }
  ]
}
                    |
                    v
Backend parses request, extracts latest message
                    |
                    v
Restore chat history to agent.messages
                    |
                    v
Call agent("Transfer patient to empty bed")
                    |
                    v
Agent thinks: <thinking>I need to query first...</thinking>
Agent calls: execute_sql_query tool
Agent thinks: <thinking>Found empty bed...</thinking>
Agent calls: assign_bed tool
Agent generates final answer
                    |
                    v
extract_text_from_messages -> all thinking + final response
parse_response_text -> separate thinking and answer
                    |
                    v
Generate SSE event stream:
  reasoning-start -> reasoning-delta -> reasoning-end
  text-start -> text-delta -> text-end
  finish
                    |
                    v
Frontend parses SSE events
Update message.parts:
  [{ type: 'reasoning', text: '...' }, { type: 'text', text: '...' }]
                    |
                    v
ReasoningBlock renders thinking
Markdown renders answer
```

---

## 关键文件总结

| 文件 | 作用 |
|------|------|
| `api/index.py` | FastAPI 后端入口，处理 `/api/chat` 请求 |
| `labor_ward_ai/ai_sdk_adapter.py` | 格式转换：AI SDK ↔ Agent 消息格式 |
| `labor_ward_ai/agent_debugger.py` | 从 Agent 消息提取 thinking 和 answer |
| `components/chat/message.tsx` | 前端消息组件，渲染 ReasoningBlock |

---

## 常见问题

### Q: 为什么每次请求都要发送完整历史？

**答：** HTTP 请求是无状态的。服务器不会自动记住之前的对话。前端（Vercel AI SDK）负责存储对话历史，每次请求都发送完整历史，后端恢复到 Agent。

这是最简单的方案。真实产品会用 session 管理，在服务端存储历史，只发送 session ID。

### Q: 为什么要分离 thinking 和 response？

**答：** 透明度与用户体验的平衡：
- 只显示最终回答 → Agent 像个黑箱，用户不知道它怎么得出结论
- 全部显示 → 信息量太大，打扰用户

折叠的 Thinking 块是最佳方案：默认收起，想看可以展开。

### Q: 为什么用 SSE 而不是普通 JSON 响应？

**答：** 用户体验。如果等 Agent 全部执行完再返回，用户可能要等 10-20 秒才看到响应。SSE 允许「边生成边发送」，用户能实时看到进度。

### Q: Agent 的 stdout 输出去哪了？

**答：** 我们用 `sys.stdout = io.StringIO()` 临时重定向了。Strands Agent 默认会打印思考过程到控制台，在 API 中我们不需要这些输出。实际的思考内容我们通过 `extract_text_from_messages` 从 Agent 消息中提取。

---

## 调试技巧

### 1. 查看请求内容

后端会把请求内容打印到 stderr（服务器日志）。查看终端输出可以看到前端发送的完整消息。

### 2. 使用浏览器开发者工具

打开浏览器的 Network 面板，找到 `/api/chat` 请求：
- **Request** 标签：查看发送的 JSON
- **Response** 标签：查看 SSE 事件流

### 3. 本地测试 Agent

在修改 API 代码之前，先用 `scripts/test_agent.py` 测试 Agent 是否正常工作。详见 [12-testing-agent-locally-CN.md](./12-testing-agent-locally-CN.md)。

---

## 总结

| 要点 | 说明 |
|------|------|
| **请求格式** | 前端发送完整对话历史，后端恢复到 Agent |
| **消息分离** | thinking 取全部消息，response 只取最后一个 |
| **SSE 协议** | reasoning-start/delta/end + text-start/delta/end |
| **前端渲染** | ReasoningBlock 显示 thinking，Markdown 显示 response |
| **状态管理** | 前端存储历史，后端无状态 |

**核心思想：**

把 AI Agent 连接到 UI，需要解决两个问题：
1. **「思考过程」和「最终回答」的分离显示** — 让用户能看到 Agent 是怎么工作的
2. **多轮对话的历史管理** — 让 Agent 能「记住」之前说了什么

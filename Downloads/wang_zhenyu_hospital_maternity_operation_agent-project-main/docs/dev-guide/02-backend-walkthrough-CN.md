# 后端代码详解

本文档详细介绍后端代码的目录结构、每个文件的职责，以及 AWS Bedrock 的调用流程。

---

## 目录结构

```
├── api/                           # FastAPI 入口（Vercel Serverless）
│   └── index.py                   # 所有 API 路由定义
│
└── labor_ward_ai/             # 核心业务逻辑
    ├── __init__.py
    ├── config.py                  # 配置管理（环境检测、AWS credentials）
    ├── runtime.py                 # 运行时检测（local vs Vercel）
    ├── paths.py                   # 文件路径枚举（prompts 位置）
    ├── boto_ses.py                # boto3 Session / Client 初始化
    ├── multi_round_bedrock_runtime_chat_manager.py  # Bedrock 多轮对话管理
    ├── ai_sdk_adapter.py          # AI SDK ↔ Bedrock 格式转换
    ├── utils.py                   # 工具函数
    └── prompts/                   # Prompt 模板
        ├── instruction.md         # System Prompt（AI 行为定义）
        └── knowledge-base.md      # 知识库（AI 参考的背景信息）
```

---

## 关键文件详解

### `api/index.py` - API 入口

这是 FastAPI 应用的入口，定义了两个端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/hello` | GET | 健康检查 |
| `/api/chat` | POST | 主聊天端点，处理 AI 对话 |

**`/api/chat` 核心流程：**

```python
@app.post("/api/chat")
async def handle_chat_data(request: Request):
    # 1. 解析 AI SDK 请求格式
    request_body = RequestBody(**request_body_data)

    # 2. 初始化 Bedrock 会话
    chat_session = ChatSession(
        client=bedrock_runtime_client,
        model_id=config.model_id,
        system=[{"text": path_enum.instruction_content}],  # System Prompt
    )

    # 3. 注入知识库
    chat_session._messages = [
        {"role": "user", "content": [{"text": knowledge_base_content}]},
        {"role": "assistant", "content": [{"text": "I've reviewed..."}]},
    ]

    # 4. 追加前端传来的对话历史
    messages = request_body_to_bedrock_converse_messages(request_body)
    chat_session._messages.extend(messages)

    # 5. 调用 Bedrock 生成回复
    response = chat_session.send_message([])

    # 6. 返回 SSE Streaming 响应
    return StreamingResponse(ai_sdk_message_generator(output_text))
```

---

### `labor_ward_ai/config.py` - 配置管理

**设计模式：** Config Pattern

核心思想：把所有环境相关的配置集中在一个地方，其他代码只需要 `from config import config` 即可。

```python
@dataclasses.dataclass
class Config:
    aws_region: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    model_id: str | None

    @classmethod
    def new_in_local_runtime(cls):
        # 本地开发：使用 ~/.aws/credentials
        return cls(aws_region="us-east-1")

    @classmethod
    def new_in_vercel_runtime(cls):
        # Vercel：从环境变量读取
        return cls(
            aws_region="us-east-1",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )

# 单例，启动时自动检测环境
config = Config.new()
```

**好处：** 添加新配置只需修改这一个文件，不需要到处加 `if runtime.is_vercel()` 检查。

---

### `labor_ward_ai/runtime.py` - 运行时检测

检测当前是本地开发还是 Vercel 环境：

```python
class Runtime:
    def is_local(self) -> bool:
        return not self.is_vercel()

    def is_vercel(self) -> bool:
        return os.environ.get("VERCEL", "0") == "1"

runtime = Runtime()
```

---

### `labor_ward_ai/multi_round_bedrock_runtime_chat_manager.py` - 对话管理

封装 AWS Bedrock Converse API，管理多轮对话：

```python
@dataclasses.dataclass
class ChatSession:
    client: "Client"           # boto3 Bedrock Runtime client
    model_id: str              # e.g., "us.amazon.nova-micro-v1:0"
    system: Sequence[...]      # System Prompt
    _messages: list            # 对话历史

    def send_message(self, content):
        """发送消息并获取 AI 回复"""
        response = self.client.converse(
            modelId=self.model_id,
            system=self.system,
            messages=self._messages,
        )
        return response
```

**功能：**
- 自动管理对话历史
- 封装 Bedrock API 调用
- 提供调试方法

---

### `labor_ward_ai/ai_sdk_adapter.py` - 格式转换

AI SDK（前端）和 Bedrock（后端）使用不同的消息格式，这个模块负责转换：

**AI SDK 格式：**
```json
{
  "messages": [
    {"role": "user", "parts": [{"type": "text", "text": "Hello"}]}
  ]
}
```

**Bedrock 格式：**
```json
{
  "messages": [
    {"role": "user", "content": [{"text": "Hello"}]}
  ]
}
```

**关键函数：**
- `request_body_to_bedrock_converse_messages()` - 批量转换消息列表
- `ai_sdk_message_generator()` - 生成 AI SDK Data Stream 格式的响应

---

### `labor_ward_ai/boto_ses.py` - AWS Client 初始化

根据配置创建 boto3 Session 和 Bedrock Runtime Client：

```python
# 根据 config 决定是否传入显式 credentials
session = boto3.Session(
    region_name=config.aws_region,
    aws_access_key_id=config.aws_access_key_id,
    aws_secret_access_key=config.aws_secret_access_key,
)

bedrock_runtime_client = session.client("bedrock-runtime")
```

---

### `labor_ward_ai/prompts/` - Prompt 模板

| 文件 | 用途 |
|------|------|
| `bi-agent-system-prompt.md` | System Prompt，定义 AI Agent 的行为、工具使用指南和工作流程 |

这些文件通过 `paths.py` 加载，在 Agent 初始化时注入。

---

## 数据流

```
前端 useChat()
    ↓ POST /api/chat (AI SDK 格式)
api/index.py
    ↓ 解析请求
    ↓ 恢复对话历史
    ↓ 调用 Strands Agent
    ↓
Agent (思考 + 调用工具)
    ↓ 可能调用 get_database_schema
    ↓ 可能调用 execute_sql_query
    ↓ 可能调用 write 操作工具
    ↓
AWS Bedrock (Claude)
    ↓ 返回响应
    ↓
ai_sdk_adapter
    ↓ 分离 thinking 和 response
    ↓ 转换为 AI SDK Data Stream 格式
    ↓ SSE Streaming (reasoning + text)
前端 useChat() 渲染
```

---

## Python 依赖说明

| 包名 | 用途 |
|------|------|
| `fastapi` | Web 框架 |
| `uvicorn` | ASGI 服务器 |
| `boto3` | AWS SDK |
| `vercel-ai-sdk-mate` | AI SDK 请求/响应格式解析 |
| `boto3-dataclass-bedrock-runtime` | Bedrock 响应类型化 |
| `func-args` | 可选参数处理 |

---

## 添加新功能的位置

| 需求 | 修改位置 |
|------|----------|
| 换 AI 模型 | `config/conf_00_def.py` 的 `model_id` |
| 改 System Prompt | `prompts/bi-agent-system-prompt.md` |
| 添加新 API 端点 | `api/index.py` |
| 添加新配置项 | `config/conf_00_def.py` |
| 添加新 Agent 工具 | `one/one_04_agent.py` |

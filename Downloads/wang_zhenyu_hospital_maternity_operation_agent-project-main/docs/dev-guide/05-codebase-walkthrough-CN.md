# 代码库架构概览

本文档提供项目的高层架构视图，帮助你快速理解代码组织结构。

---

## 项目结构

```
labor_ward_ai-project/
│
├── labor_ward_ai/      # Python 后端核心代码，包含 AI Agent、数据库连接、配置管理等所有业务逻辑
├── tests_python/           # Python 测试文件，用 pytest 框架运行，验证后端代码是否正常工作
├── api/                    # FastAPI 入口文件，部署到 Vercel 时作为 Serverless Function 运行
├── app/                    # Next.js 前端页面，用户看到的聊天界面就在这里
├── components/             # React 组件库，包含按钮、输入框、聊天气泡等可复用的 UI 组件
├── mise.toml               # 开发任务配置文件，定义了 `mise run dev` 等快捷命令和工具版本
├── pyproject.toml          # Python 项目配置文件，列出了所有需要安装的 Python 包（如 FastAPI、boto3）
└── package.json            # Node.js 项目配置文件，列出了所有需要安装的前端包（如 React、Next.js）
```

---

## labor_ward_ai 模块结构

这是整个项目的「大脑」，所有后端逻辑都在这里。

```
labor_ward_ai/
│
├── api.py                  # 对外暴露的入口文件，其他代码通过 `from labor_ward_ai.api import one` 获取主对象
├── paths.py                # 路径管理器，把项目里所有重要的文件路径集中定义在一起，避免到处写死路径字符串
├── runtime.py              # 运行环境检测器，自动判断代码是跑在你的电脑上（local）还是云端服务器上（vercel）
├── constants.py            # 常量和枚举定义，比如数据库表名、状态码等不会变的值，集中放在这里方便维护
├── write_operations.py     # 数据库写入函数，包含分配床位、创建订单等修改数据库的操作，每个函数都是独立的
├── sql_utils.py            # SQL 工具函数，负责执行 SQL 查询并把结果格式化成好看的 Markdown 表格
├── ai_sdk_adapter.py       # 格式转换器，把前端发来的消息格式转成 AWS Bedrock 能理解的格式，反之亦然
│
├── config/                 # 配置相关代码的文件夹
│   └── conf_00_def.py      # 配置类定义，读取环境变量（如数据库密码、AWS 密钥）并提供给其他代码使用
│
├── one/                    # 主类和 Mixin 的文件夹，采用「组合模式」把不同功能拆分到不同文件
│   ├── one_00_main.py      # 主类 One，通过继承把下面所有 Mixin 的功能组合在一起，是整个后端的核心对象
│   ├── one_01_config.py    # ConfigMixin，给主类添加 `self.config` 属性，用于读取配置信息
│   ├── one_02_db.py        # DbMixin，给主类添加数据库连接能力，提供 `self.engine` 用于执行 SQL
│   ├── one_03_boto3.py     # Boto3Mixin，给主类添加 AWS 服务访问能力，可以调用 Bedrock AI 模型
│   ├── one_04_agent.py     # AgentMixin，给主类添加 AI Agent 能力，定义了 Agent 可以使用的各种工具
│   └── api.py              # 创建并导出 `one = One()` 单例对象，整个程序只有这一个实例
│
├── prompts/                # AI 提示词模板文件夹，存放给 AI 的指令
│   └── bi-agent-system-prompt.md  # Agent 的系统提示词，告诉 AI 它的角色是什么、应该如何回答问题
│
└── db_schema/              # 数据库 Schema 相关文件，把数据库结构转换成 AI 容易理解的文本格式
```

---

## 类继承结构

`One` 类采用 Mixin 模式，把不同功能拆分到不同的类中，然后组合在一起。这样代码更容易维护。

```
One (one_00_main.py)
│   Main class, inherits all Mixins below, has config/db/AWS/Agent capabilities
│
├── ConfigMixin (one_01_config.py)
│   │   Provides configuration reading capability
│   └── self.config  →  Contains db password, AWS keys, and other sensitive configs
│
├── DbMixin (one_02_db.py)
│   │   Provides database operation capability
│   ├── self.engine  →  Database connection object for executing SQL queries
│   └── self.database_schema_str  →  Text description of db schema for AI reference
│
├── Boto3Mixin (one_03_boto3.py)
│   │   Provides AWS service access capability
│   └── self.bedrock_runtime_client()  →  Bedrock client for calling Claude AI model
│
└── AgentMixin (one_04_agent.py)
        Provides AI Agent capability
    ├── self.agent  →  Agent object that understands questions and calls tools
    └── @tool methods  →  Tool functions Agent can use (query db, assign beds, etc.)
```

---

## 数据流

当用户在聊天界面发送消息时，数据会按以下路径流动：

```
┌──────────────────────────────────────────────────────────────┐
│  User Input (Chat UI)                                        │
│  User types a question in the chat box and clicks send       │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  Next.js Frontend                                            │
│  Frontend receives input, sends HTTP request via useChat     │
│  - useChat hook (Vercel AI SDK)                              │
│  - POST /api/chat                                            │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Backend (api/index.py)                              │
│  Backend API receives request, parses message, calls Agent   │
│  - Parse request (ai_sdk_adapter.py)                         │
│  - Call Agent (one.agent)                                    │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  Strands Agent (one_04_agent.py)                             │
│  Agent analyzes question, decides which tools to use         │
│  - System prompt from prompts/                               │
│  - Tools: get_schema, execute_sql, write_report              │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  AWS Bedrock (LLM)                                           │
│  Cloud AI model (e.g. Claude) generates response text        │
│  - Model: configurable via config.model_id                   │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  SSE Streaming Response                                      │
│  AI response streams back to frontend character by character │
│  - AI SDK v5 Data Stream Protocol                            │
└──────────────────────────────────────────────────────────────┘
```

---

## tests_python 测试结构

测试文件的命名规则：`test_<模块名>.py` 或 `test_<文件夹>_<文件名>.py`。

```
tests_python/
│
├── config/
│   └── test_config_conf_00_def.py   # 测试配置类是否能正确读取环境变量
│
├── one/
│   ├── test_one_one_00_main.py      # 测试主类 One 是否能正常初始化
│   ├── test_one_one_01_config.py    # 测试 ConfigMixin 是否正常工作
│   └── test_one_one_02_db.py        # 测试 DbMixin 的数据库连接功能
│
├── test_api.py                      # 测试 api.py 的导出是否正确
├── test_write_operations.py         # 测试数据库写入函数是否正常工作
└── test_utils.py                    # 测试工具函数
```

---

## 关键单例

整个程序中有三个重要的「单例」对象，它们在程序启动时创建一次，之后到处使用同一个实例：

```python
from labor_ward_ai.api import one           # 主对象，包含 Agent、数据库、配置等所有能力
from labor_ward_ai.paths import path_enum   # 路径对象，通过它获取项目中各种文件的路径
from labor_ward_ai.runtime import runtime   # 运行时对象，用于判断当前是本地开发还是云端部署
```

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `mise run inst` | 安装所有依赖（Python + Node.js 的包都会装好） |
| `mise run dev` | 启动开发服务器（前端 + 后端同时启动，改代码会自动刷新） |
| `mise run test` | 运行所有测试（确保代码没有 bug） |
| `mise run test-python` | 仅运行 Python 测试 |

---

## 下一步

各模块的详细说明请参考后续文档。

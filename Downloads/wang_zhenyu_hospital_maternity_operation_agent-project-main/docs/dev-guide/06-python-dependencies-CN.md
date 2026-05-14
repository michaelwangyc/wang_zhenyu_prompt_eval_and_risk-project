# Python 依赖详解

本文档面向刚接触 Python、没有安装过依赖的新手，详细介绍 `pyproject.toml` 文件和项目依赖。

---

## 什么是 pyproject.toml？

`pyproject.toml` 是 Python 项目的**配置文件**，用 TOML 格式编写。

**类比理解：**

想象你要做一道菜。`pyproject.toml` 就像一份**食谱**：
- 菜名是什么（项目名称）
- 需要哪些食材（依赖库）
- 每种食材要多少（版本范围）

有了这份食谱，任何人都能买到相同的食材，做出相同的菜。

**文件结构：**

```toml
[project]
name = "labor_ward_ai"       # 项目名称
version = "0.1.1"                # 项目版本
requires-python = ">=3.12,<4.0"  # 需要 Python 3.12 或更高版本

dependencies = [
    "fastapi>=0.118.0,<1.0.0",   # 依赖库列表
    # ...
]
```

---

## 什么是 Dependencies（依赖）？

**Dependencies**（依赖）是你的项目需要用到的**第三方库**。

**为什么需要依赖？**

写代码时，很多功能不需要从零开始写。比如：
- 想搭建 Web API？用 `fastapi`
- 想连接 AWS？用 `boto3`
- 想操作数据库？用 `SQLAlchemy`

这些库是别人已经写好的代码，你只需要**安装**它们，然后 `import` 进来用。

**怎么安装？**

我们用 `uv`（一个现代 Python 包管理工具）来安装：

```bash
# mise 会自动调用 uv 安装所有依赖
mise run inst
```

安装后，这些库会出现在 `.venv/` 目录里，你的代码就能 `import` 它们了。

---

## 每个依赖库是干什么的？

下面逐一介绍项目中的每个依赖库。

### Web 框架相关

| 库名 | 用途 | PyPI 链接 |
|------|------|-----------|
| **fastapi** | Web 框架，用来写 API 接口 | [pypi.org/project/fastapi](https://pypi.org/project/fastapi/) |
| **uvicorn** | 运行 FastAPI 的服务器 | [pypi.org/project/uvicorn](https://pypi.org/project/uvicorn/) |
| **pydantic** | 数据验证，确保输入数据格式正确 | [pypi.org/project/pydantic](https://pypi.org/project/pydantic/) |

**人话解释：**

- **fastapi**：就像一个"接线员"。用户发请求过来，FastAPI 负责接收、处理、返回结果。我们的 `/api/chat` 接口就是用它写的。

- **uvicorn**：FastAPI 只是代码，需要有人"运行"它。uvicorn 就是那个运行它的服务器程序。就像餐厅（FastAPI）需要有人开门营业（uvicorn）。

- **pydantic**：检查数据格式。比如你期望用户传一个数字，但他传了一段文字，pydantic 会报错阻止。就像保安检查入场证件。

---

### AWS 和 AI 相关

| 库名 | 用途 | PyPI 链接 |
|------|------|-----------|
| **boto3** | AWS 官方 SDK，用来调用 AWS 服务 | [pypi.org/project/boto3](https://pypi.org/project/boto3/) |
| **boto3-dataclass** | 把 boto3 返回的数据变成有类型提示的对象 | [pypi.org/project/boto3-dataclass](https://pypi.org/project/boto3-dataclass/) |
| **strands-agents** | AI Agent 框架，让 AI 能使用工具 | [pypi.org/project/strands-agents](https://pypi.org/project/strands-agents/) |
| **strands-agents-tools** | strands-agents 的工具集 | [pypi.org/project/strands-agents-tools](https://pypi.org/project/strands-agents-tools/) |

**人话解释：**

- **boto3**：AWS 的"遥控器"。想调用 Bedrock（AI 服务）？用 boto3 发指令。想操作 S3（存储）？也用 boto3。所有 AWS 服务都通过它控制。

- **boto3-dataclass**：boto3 返回的数据是"字典"格式，不好用。这个库把它变成有代码提示的对象，写代码时 IDE 能自动补全。

- **strands-agents**：AI Agent 框架。普通 AI 只能对话；Agent 能"使用工具"——比如查数据库、调 API。这个框架让我们能定义工具、让 AI 自主决定何时调用。

- **strands-agents-tools**：strands-agents 的配套工具包，提供一些现成的工具实现。

---

### 数据库相关

| 库名 | 用途 | PyPI 链接 |
|------|------|-----------|
| **SQLAlchemy** | 数据库操作工具，支持多种数据库 | [pypi.org/project/SQLAlchemy](https://pypi.org/project/SQLAlchemy/) |
| **psycopg2-binary** | PostgreSQL 数据库驱动 | [pypi.org/project/psycopg2-binary](https://pypi.org/project/psycopg2-binary/) |

**人话解释：**

- **SQLAlchemy**：操作数据库的"翻译官"。你写 Python 代码，它翻译成 SQL 语句发给数据库。支持 SQLite、PostgreSQL、MySQL 等多种数据库。

- **psycopg2-binary**：专门连接 PostgreSQL 的"插头"。SQLAlchemy 是通用翻译官，但连接具体数据库需要专门的驱动。连 PostgreSQL 就用这个。`-binary` 表示预编译版本，安装更简单。

---

### 前端协议适配

| 库名 | 用途 | PyPI 链接 |
|------|------|-----------|
| **vercel-ai-sdk-mate** | 适配 Vercel AI SDK 的消息格式 | [pypi.org/project/vercel-ai-sdk-mate](https://pypi.org/project/vercel-ai-sdk-mate/) |

**人话解释：**

- **vercel-ai-sdk-mate**：前端（React）用 Vercel AI SDK，后端（Python）用 Bedrock，两边"说的语言不一样"。这个库负责翻译，让它们能互相理解。

---

### 工具类

| 库名 | 用途 | PyPI 链接 |
|------|------|-----------|
| **rich** | 在终端打印漂亮的文字、表格、进度条 | [pypi.org/project/rich](https://pypi.org/project/rich/) |
| **tabulate** | 把数据格式化成表格 | [pypi.org/project/tabulate](https://pypi.org/project/tabulate/) |
| **fire** | 把 Python 函数变成命令行工具 | [pypi.org/project/fire](https://pypi.org/project/fire/) |
| **python-dotenv** | 从 `.env` 文件读取环境变量 | [pypi.org/project/python-dotenv](https://pypi.org/project/python-dotenv/) |
| **func-args** | 检查函数参数 | [pypi.org/project/func-args](https://pypi.org/project/func-args/) |
| **enum_mate** | 增强版枚举类型 | [pypi.org/project/enum-mate](https://pypi.org/project/enum-mate/) |

**人话解释：**

- **rich**：让终端输出变漂亮。普通 `print()` 只能打印黑白文字，用 rich 可以打印彩色文字、表格、进度条。调试时看起来更清晰。

- **tabulate**：把数据变成表格字符串。比如 SQL 查询结果，用它格式化后变成整齐的 Markdown 表格。

- **fire**：把函数变成命令行命令。写一个函数，用 fire 包一下，就能在终端用 `python script.py --参数=值` 的方式调用。

- **python-dotenv**：读 `.env` 文件。数据库密码、API 密钥等敏感信息放在 `.env` 里，这个库帮你读出来变成环境变量。

- **func-args**：检查函数有哪些参数。Agent 框架用它来读取工具函数的参数定义。

- **enum_mate**：增强版枚举。Python 自带的 `enum` 功能有限，这个库增加了一些便利功能。

---

## 版本范围是什么意思？

你可能注意到每个依赖后面都有版本号：

```toml
"fastapi>=0.118.0,<1.0.0"
```

这是什么意思？

### 版本号格式

版本号通常是 `主版本.次版本.补丁版本`，比如 `0.118.0`：
- **主版本 (0)**：大改动，可能不兼容旧代码
- **次版本 (118)**：新功能，保持兼容
- **补丁版本 (0)**：修复 bug，保持兼容

### 版本范围符号

| 符号 | 含义 | 示例 |
|------|------|------|
| `>=` | 大于等于 | `>=0.118.0` 表示 0.118.0 或更高 |
| `<` | 小于 | `<1.0.0` 表示不能是 1.0.0 或更高 |
| `==` | 精确等于 | `==0.118.0` 表示必须是这个版本 |

### 为什么要写范围？

```toml
"fastapi>=0.118.0,<1.0.0"
```

这行的意思是：**至少是 0.118.0，但不能到 1.0.0**。

**为什么不直接写死一个版本？**

1. **允许安全更新**：如果 fastapi 发布了 0.118.1 修复了安全漏洞，你的项目可以自动用上。

2. **避免破坏性更新**：1.0.0 可能有大改动，不兼容你的代码。限制 `<1.0.0` 保护你不会意外升级到不兼容的版本。

**类比理解：**

就像说"我要一双 Nike 运动鞋，42 码或 42.5 码都行，但不要 43 码"。有一定灵活性，但不能差太多。

---

## uv 是怎么安装依赖的？

你在 `pyproject.toml` 里写的是**版本范围**，但实际安装时需要确定**具体版本**。这个工作由 `uv` 完成。

### 什么是 uv？

`uv` 是一个现代 Python 包管理工具，速度极快（用 Rust 写的）。它做两件事：

1. **解析依赖**：算出每个库应该装哪个具体版本
2. **安装依赖**：下载并安装这些库

### 依赖解析是什么？

想象一下这个场景：

- 你的项目需要 `fastapi>=0.118.0`
- `fastapi` 又需要 `pydantic>=2.0.0`
- 但你的项目还需要 `strands-agents`，它需要 `pydantic>=2.5.0,<3.0.0`

所有这些要求必须**同时满足**。这就是一个**约束求解问题**。

### uv 的解析过程（简化版）

```
你的需求：
  fastapi >= 0.118.0
  pydantic >= 2.11.10
  strands-agents >= 1.26.0

fastapi 0.118.0 需要：
  pydantic >= 2.0.0
  starlette >= 0.37.0

strands-agents 1.26.0 需要：
  pydantic >= 2.5.0, < 3.0.0

uv 计算：
  pydantic 必须 >= 2.11.10 (你的要求)
  pydantic 必须 >= 2.5.0, < 3.0.0 (strands-agents 的要求)
  → 交集：pydantic 2.11.10 满足所有条件 ✓

最终结果：
  fastapi==0.118.0
  pydantic==2.11.10
  strands-agents==1.26.0
  starlette==0.37.0
  ...
```

这个过程涉及**数学优化**——在满足所有约束的前提下，找到一组兼容的版本组合。有时候约束互相冲突，uv 会报错告诉你"无法解析"。

### 锁定文件 uv.lock

解析完成后，uv 会生成 `uv.lock` 文件，记录每个库的**精确版本**：

```toml
# uv.lock (示例)
[[package]]
name = "fastapi"
version = "0.118.0"

[[package]]
name = "pydantic"
version = "2.11.10"
```

**为什么需要锁定文件？**

- `pyproject.toml` 说的是"范围"（食谱）
- `uv.lock` 说的是"精确版本"（购物清单）

有了锁定文件，团队每个人安装的都是**完全相同的版本**，避免"在我电脑上能跑"的问题。

### 安装命令

```bash
# 安装依赖（会读 uv.lock，如果没有则先解析）
uv sync

# 我们项目用 mise 封装了这个命令
mise run inst
```

---

## 总结

| 概念 | 作用 |
|------|------|
| `pyproject.toml` | 定义项目需要哪些依赖（食谱） |
| dependencies | 第三方库列表 |
| 版本范围 | 允许一定灵活性，同时避免破坏性更新 |
| uv | 解析版本约束 + 安装依赖 |
| `uv.lock` | 锁定精确版本，保证环境一致 |

**记住这个流程：**

```
pyproject.toml (版本范围)
       ↓
    uv 解析
       ↓
  uv.lock (精确版本)
       ↓
    uv 安装
       ↓
  .venv/ (安装好的库)
       ↓
  你的代码可以 import 了
```

# 项目架构总览

这是一个 AI Agent 学习项目，目标是构建一个 OB/GYN（妇产科）病房的 AI 排班助手。护士可以通过自然语言查询病房状态、预测患者住院时长、协调床位分配、接收高风险警报。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js 16 + React 18 | App Router，TypeScript |
| UI | Tailwind CSS + Radix UI | 样式系统 + 无障碍组件库 |
| AI 前端 | Vercel AI SDK (`ai`, `@ai-sdk/react`) | 处理 streaming 响应 |
| 后端 | FastAPI (Python 3.12) | REST API，处理 AI 请求 |
| AI 后端 | AWS Bedrock (Claude) | LLM 服务 |
| 部署 | Vercel | 前端 + Serverless Functions |

---

## 目录结构

```
├── app/                    # Next.js 前端 (App Router)
│   ├── (marketing)/        # Landing Page 路由组
│   ├── chat/               # Chat 页面
│   ├── layout.tsx          # 根布局
│   └── globals.css         # 全局样式
│
├── components/             # React 组件
│   ├── chat/               # Chat 相关组件
│   └── ui/                 # shadcn/ui 基础组件
│
├── lib/                    # 前端工具函数
├── data/                   # 静态数据 (stats, suggested actions)
├── hooks/                  # React Hooks
│
├── api/                    # FastAPI 入口 (Vercel Serverless)
│   └── index.py            # 所有 API 路由定义
│
├── labor_ward_ai/   # 后端核心逻辑
│   ├── config.py                  # 配置管理
│   ├── multi_round_bedrock_runtime_chat_manager.py  # Bedrock 调用
│   ├── ai_sdk_adapter.py          # AI SDK 协议适配
│   └── prompts/                   # System Prompt 模板
│
├── mise.toml               # 开发环境配置 + 任务定义
├── package.json            # Node.js 依赖
├── pyproject.toml          # Python 依赖
└── vercel.json             # Vercel 部署配置
```

---

## 数据流

```
用户输入 → Next.js 前端 → /api/chat (FastAPI)
                              ↓
                         Bedrock (Claude)
                              ↓
                    Streaming 响应 (AI SDK 协议)
                              ↓
                         前端渲染消息
```

---

## 在 MacOS / Linux 上运行项目

### 前置条件

1. 安装 [mise](https://mise.jdx.dev/)（版本管理 + 任务运行器）
2. AWS 账号配置好 Bedrock 访问权限

### 步骤

```bash
# 1. 克隆项目
git clone <repo-url>
cd labor_ward_ai-project

# 2. 让 mise 安装工具链 (Python 3.12, Node 24, pnpm, uv)
mise install

# 3. 创建 Python 虚拟环境
mise run venv-create

# 4. 安装所有依赖 (Python + Node.js)
mise run inst

# 5. 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，填入 AWS credentials 等

# 6. 启动开发服务器 (Next.js + FastAPI)
mise run dev
```

启动后：
- 前端: http://localhost:3000
- 后端: http://localhost:8000
- Chat 页面: http://localhost:3000/chat

### 常用 mise 命令

| 命令 | 说明 |
|------|------|
| `mise run dev` | 启动前端 + 后端开发服务器 |
| `mise run kill` | 停止所有开发服务器 |
| `mise run test` | 运行所有测试 |
| `mise run inst` | 安装所有依赖 |

---

## 部署

项目部署到 Vercel：
- 前端由 Next.js 处理
- 后端 FastAPI 作为 Serverless Function 运行（见 `vercel.json` 和 `api/index.py`）

环境变量需要在 Vercel Dashboard 中配置。

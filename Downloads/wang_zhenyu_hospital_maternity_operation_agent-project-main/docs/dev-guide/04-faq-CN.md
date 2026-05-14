# 常见问题与操作手册

本文档包含常见的代码修改需求示例、Debug 技巧和部署流程。

---

## 前端代码修改示例

### 1. 修改网站标题和元数据

**需求：** 修改网站标题和描述

**修改位置：** `lib/constants.ts`

```ts
export const METADATA = {
  TITLE: "MaterniFlow - OB/GYN Ward Assistant",  // 改这里
  DESCRIPTION: "AI scheduling assistant for OB/GYN wards",
  AI_ASSISTANT_NAME: "MaterniFlow Agent",
};
```

**影响范围：** 浏览器标签页标题、SEO meta 标签

---

### 2. 修改 Chat 页面的快捷按钮

**需求：** 添加或修改聊天页面的预设问题按钮

**修改位置：** `data/suggested-actions.json`

```json
[
  {
    "title": "Ward Status",
    "label": "Show current ward status",
    "action": "What is the current ward status?"
  },
  {
    "title": "Available Beds",
    "label": "Find available beds",
    "action": "Which beds are currently available?"
  }
]
```

**影响范围：** `components/chat/multimodal-input.tsx` 读取此文件

---

### 4. 修改 UI 样式（颜色、字体等）

**需求：** 更改主题颜色或字体

**修改位置：**
- 颜色变量：`app/globals.css` 的 CSS 变量
- 字体：`app/layout.tsx` 的 Google Fonts 导入
- Tailwind 配置：`tailwind.config.ts`

```css
/* app/globals.css */
:root {
  --accent: 210 100% 50%;  /* 修改强调色 */
}
```

---

## 后端代码修改示例

### 1. 修改 AI Agent 的 System Prompt

**需求：** 调整 Agent 的行为、工具使用指南或工作流程

**修改位置：** `labor_ward_ai/prompts/bi-agent-system-prompt.md`

```markdown
You are a helpful AI assistant for OB/GYN ward scheduling.
Your role is to help nurses query ward status, manage beds...
```

**注意：** 这个文件在 Agent 初始化时作为 system prompt 传入

---

### 2. 切换 AI 模型

**需求：** 切换到其他模型

**修改位置：** `labor_ward_ai/config/conf_00_def.py`

```python
@dataclasses.dataclass
class Config:
    model_id: str | None = dataclasses.field(
        default="us.anthropic.claude-sonnet-4-20250514-v1:0"  # 改这里
    )
```

**可用模型：** 查看 AWS Bedrock Console 获取支持的 Model ID

---

### 3. 添加新的 API 端点

**需求：** 添加一个新的 API 端点

**修改位置：** `api/index.py`

```python
@app.get("/api/health")
async def health_check():
    return JSONResponse(content={
        "status": "ok",
        "service": "MaterniFlow Agent",
    })
```

**注意：** Vercel 会自动将 `api/index.py` 部署为 Serverless Function

---

## Debug 技巧

### 1. 查看前端 AI SDK 请求

打开浏览器开发者工具 → Network → 过滤 `chat` → 查看 Request Payload

```json
{
  "messages": [...],
  "id": "session-id"
}
```

### 2. 查看后端日志

本地开发时，FastAPI 日志会打印在终端。关键日志位置：

- `api/index.py` 中的 `debug_ai_sdk_request()` 会打印请求内容
- `ChatSession.debug_response()` 会打印 Bedrock 响应

### 3. 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `403 Forbidden` from Bedrock | AWS credentials 无效或无权限 | 检查 `~/.aws/credentials` 或环境变量 |
| `useChat` 不更新 | API 返回格式不对 | 确保返回 AI SDK Data Stream 格式 |
| CORS 错误 | 跨域请求被拒绝 | Next.js rewrites 应该处理，检查 `next.config.js` |
| 消息不显示 | SSE 响应格式错误 | 检查 `ai_sdk_message_generator()` 输出 |

### 4. 本地测试 API

```bash
# 测试 hello 端点
curl http://localhost:8000/api/hello

# 测试 chat 端点
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "parts": [{"type": "text", "text": "Hello"}]}], "id": "test"}'
```

---

## 开发环境设置

### 首次设置

```bash
# 1. 安装 mise
curl https://mise.jdx.dev/install.sh | sh

# 2. 让 mise 安装工具链
mise install

# 3. 创建虚拟环境 + 安装依赖
mise run venv-create
mise run inst

# 4. 配置环境变量
cp .env.example .env.local
# 编辑 .env.local
```

### 日常开发

```bash
# 启动开发服务器
mise run dev

# 停止服务器
mise run kill

# 运行测试
mise run test
```

### 常用端口

| 服务 | 端口 | URL |
|------|------|-----|
| Next.js | 3000 | http://localhost:3000 |
| FastAPI | 8000 | http://localhost:8000 |

---

## Vercel 部署流程

### 首次部署

1. 在 GitHub 上 fork 或 push 代码
2. 登录 [Vercel Dashboard](https://vercel.com)
3. Import 项目
4. 配置环境变量：
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
5. 点击 Deploy

### 更新部署

```bash
# 推送到 main 分支会自动触发部署
git push origin main
```

### 环境变量管理

| 变量 | 用途 | 在哪配置 |
|------|------|----------|
| `AWS_ACCESS_KEY_ID` | AWS 访问密钥 | Vercel Dashboard → Settings → Environment Variables |
| `AWS_SECRET_ACCESS_KEY` | AWS 密钥 | 同上 |
| `AWS_DEFAULT_REGION` | AWS 区域 | 同上 |
| `DB_HOST` | 数据库主机 | 同上 |
| `DB_PORT` | 数据库端口 | 同上 |
| `DB_USER` | 数据库用户名 | 同上 |
| `DB_PASS` | 数据库密码 | 同上 |
| `DB_NAME` | 数据库名称 | 同上 |
| `VERCEL` | Vercel 自动设置 | 自动 |

### 查看部署日志

Vercel Dashboard → Deployments → 选择部署 → View Build Logs / Function Logs

---

## 代码结构速查

| 要改什么 | 去哪里改 |
|----------|----------|
| 网站标题/描述 | `lib/constants.ts` |
| Landing Page 内容 | `app/(marketing)/_components/` |
| Chat UI | `components/chat/` |
| Agent System Prompt | `labor_ward_ai/prompts/bi-agent-system-prompt.md` |
| AI 模型 | `labor_ward_ai/config/conf_00_def.py` |
| Agent 工具 | `labor_ward_ai/one/one_04_agent.py` |
| API 端点 | `api/index.py` |
| 全局样式 | `app/globals.css` |
| Tailwind 配置 | `tailwind.config.ts` |

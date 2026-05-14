# 前端代码详解

本文档详细介绍前端代码的目录结构、每个文件的职责，以及 AI SDK 的使用方式。

---

## 目录结构

```
├── app/                          # Next.js App Router
│   ├── layout.tsx                # 根布局：字体、主题、全局样式
│   ├── globals.css               # 全局 CSS 变量、颜色系统、工具类
│   │
│   ├── (marketing)/              # Landing Page 路由组（括号表示不影响 URL）
│   │   ├── page.tsx              # 首页入口 → 渲染 HomePageContent
│   │   ├── layout.tsx            # Marketing 布局
│   │   ├── loading.tsx           # 加载状态 UI
│   │   ├── HomePageContent.tsx   # 首页主内容组织
│   │   └── _components/          # Landing Page 专用组件
│   │       ├── Hero.tsx          # 英雄区（大标题、CTA 按钮）
│   │       ├── StatsSection.tsx  # 数据统计展示
│   │       └── ContactSection.tsx # 联系方式
│   │
│   ├── chat/                     # Chat 页面
│   │   ├── page.tsx              # Chat 页面入口 → 渲染 Chat 组件
│   │   ├── layout.tsx            # Chat 布局
│   │   └── loading.tsx           # 加载状态
│   │
│   ├── _components/              # 跨页面共享组件
│   │   ├── layouts/Navigation.tsx # 顶部导航栏
│   │   └── common/MarkdownModal.tsx
│   │
│   └── test-api/                 # API 测试页面（开发用）
│
├── components/                   # 通用 React 组件
│   ├── chat/                     # Chat 核心组件
│   │   ├── chat.tsx              # 主聊天组件（useChat Hook）
│   │   ├── message.tsx           # 单条消息渲染
│   │   ├── multimodal-input.tsx  # 输入框 + 快捷按钮
│   │   ├── overview.tsx          # Chat 欢迎屏
│   │   ├── markdown.tsx          # Markdown 渲染
│   │   └── icons/                # Chat 相关图标
│   │
│   ├── ui/                       # shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ... (50+ 组件)
│   │
│   └── theme-provider.tsx        # 主题切换 Provider
│
├── lib/                          # 工具函数
│   ├── constants.ts              # 常量（标题、CDN 链接、路由）
│   ├── utils.ts                  # 工具函数（cn 合并类名）
│   └── seo/                      # SEO 相关
│
├── data/                         # 静态数据
│   ├── achievement-stats.ts      # Landing Page 统计数据
│   └── suggested-actions.json    # Chat 快捷按钮配置
│
├── hooks/                        # 自定义 React Hooks
│   └── use-scroll-to-bottom.ts   # 自动滚动到底部
│
├── types/                        # TypeScript 类型定义
├── public/                       # 静态资源（图片等）
└── styles/                       # 额外样式
```

---

## 关键文件详解

### `app/layout.tsx` - 根布局

- 定义全局字体（Bebas Neue 标题、Source Sans 3 正文）
- 引入 `globals.css`
- 包裹 `ThemeProvider` 支持明暗主题

### `app/globals.css` - 全局样式

- CSS 变量定义颜色系统（黑白主题 + 电蓝色强调）
- 工具类：`bold-card`, `bold-button`, `bold-nav`
- 暗色模式支持

### `components/chat/chat.tsx` - 核心聊天组件

这是 AI 交互的核心，使用 Vercel AI SDK：

```tsx
import { useChat } from "@ai-sdk/react";

// useChat Hook 管理：
// - messages: 消息列表
// - status: 'idle' | 'loading' | 'streaming'
// - append: 发送新消息
const { messages, status, append } = useChat({
  api: "/api/chat",        // 后端 API 端点
  id: chatId,              // 会话 ID
  initialMessages: [],
  onError: (error) => toast.error(error.message),
});
```

**关键实现：**
1. 使用 `FingerprintJS` 生成浏览器指纹，用于用户追踪
2. 通过 `fetch` 拦截器注入自定义 Header
3. 处理 streaming 响应，实时渲染 AI 回复

### `components/chat/multimodal-input.tsx` - 输入组件

- 文本输入框
- 快捷按钮（从 `data/suggested-actions.json` 加载）
- 发送按钮
- Hover 效果处理

### `lib/constants.ts` - 常量配置

```ts
export const METADATA = {
  TITLE: "MaterniFlow - OB/GYN Ward Assistant",
  AI_ASSISTANT_NAME: "MaterniFlow Agent",
};

export const ROUTES = {
  HOME: "/",
  CHAT: "/chat",
};
```

---

## AI SDK 依赖说明

### `package.json` 中的 AI 相关依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `ai` | ^6.0.72 | Vercel AI SDK 核心，定义 streaming 协议 |
| `@ai-sdk/react` | ^3.0.79 | React Hooks (`useChat`, `useCompletion`) |

### AI SDK 工作原理

```
前端 useChat() → POST /api/chat → 后端返回 SSE Stream → useChat 解析并更新 UI
```

**协议格式：** AI SDK Data Stream Protocol
- `0:` 前缀 = 文本 chunk
- `e:` 前缀 = 错误
- `d:` 前缀 = 完成信号

前端不需要手动解析，`useChat` Hook 自动处理。

---

## 其他重要依赖

| 包名 | 用途 |
|------|------|
| `@radix-ui/*` | 无障碍 UI 组件（shadcn/ui 底层） |
| `tailwind-merge` | 智能合并 Tailwind 类名 |
| `framer-motion` | 动画库 |
| `react-markdown` | Markdown 渲染 |
| `lucide-react` | 图标库 |
| `sonner` | Toast 通知 |
| `@fingerprintjs/fingerprintjs` | 浏览器指纹生成 |

---

## 路由结构

| URL | 文件 | 说明 |
|-----|------|------|
| `/` | `app/(marketing)/page.tsx` | Landing Page |
| `/chat` | `app/chat/page.tsx` | AI Chat 页面 |
| `/test-api` | `app/test-api/page.tsx` | API 测试（开发用） |

**注意：** `(marketing)` 括号表示路由组，不影响 URL 路径。

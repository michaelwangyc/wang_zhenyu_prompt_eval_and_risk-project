# package.json Notes

This document explains the purpose of each dependency in `package.json`. Since JSON doesn't support comments, we keep our reasoning and context here for future reference.

## Versioning Strategy

- **Framework packages** (Next.js, React) - Exact versions, require manual testing when updating
- **UI components & utilities** - Caret ranges (`^`), allow automatic patch/minor updates
- **All dependencies** - Locked via `pnpm-lock.yaml` for reproducibility across machines

See `package.json.md` for details on versioning philosophy.

---

## Core Framework

- `next` - Full-stack React framework with SSR, API routes, image optimization
- `react` - JavaScript library for building user interfaces
- `react-dom` - React package for DOM rendering

---

## Radix-UI Components

Radix Primitives provides unstyled, accessible React components. We style them with Tailwind CSS.

- `@radix-ui/react-accordion` - Expandable/collapsible sections
- `@radix-ui/react-alert-dialog` - Modal alert dialogs
- `@radix-ui/react-aspect-ratio` - Maintains fixed aspect ratio containers
- `@radix-ui/react-avatar` - User profile pictures/placeholders
- `@radix-ui/react-checkbox` - Accessible checkboxes
- `@radix-ui/react-collapsible` - Collapsible content sections
- `@radix-ui/react-context-menu` - Right-click context menus
- `@radix-ui/react-dialog` - Modal dialog windows
- `@radix-ui/react-dropdown-menu` - Dropdown menus with keyboard navigation
- `@radix-ui/react-hover-card` - Hover-triggered popovers
- `@radix-ui/react-label` - Accessible form labels
- `@radix-ui/react-menubar` - Desktop application menu bars
- `@radix-ui/react-navigation-menu` - Horizontal navigation menus
- `@radix-ui/react-popover` - Floating popover panels
- `@radix-ui/react-progress` - Progress indicators
- `@radix-ui/react-radio-group` - Radio button groups
- `@radix-ui/react-scroll-area` - Custom scrollbar styling
- `@radix-ui/react-select` - Dropdown select menus
- `@radix-ui/react-separator` - Visual divider lines
- `@radix-ui/react-slider` - Range sliders and input controls
- `@radix-ui/react-slot` - Composition primitive for component slots
- `@radix-ui/react-switch` - Toggle switches
- `@radix-ui/react-tabs` - Tabbed interfaces
- `@radix-ui/react-toast` - Toast notifications
- `@radix-ui/react-toggle` - Toggle buttons
- `@radix-ui/react-toggle-group` - Groups of toggle buttons
- `@radix-ui/react-tooltip` - Hover tooltips

---

## UI Components & Libraries

- `cmdk` - Command palette/menu component
- `embla-carousel-react` - Carousel and slider functionality
- `input-otp` - One-time password input field
- `react-day-picker` - Date picker component

---

## Icons

- `lucide-react` - Modern, consistent icon library
- `react-icons` - Multiple icon packs (Font Awesome, Feather, etc.)

---

## Styling & Theme

- `class-variance-authority` - Component variant system for consistent styling
- `clsx` - Utility for conditional CSS class names
- `tailwind-merge` - Merge Tailwind CSS classes without conflicts
- `tailwindcss-animate` - Animation utilities for Tailwind
- `next-themes` - Dark/light theme switching with persistence

---

## Data Visualization

- `recharts` - React charts library built on D3

---

## Forms

- `react-hook-form` - Performant, flexible form library with validation

---

## Content Rendering

- `react-markdown` - Render Markdown as React components
- `react-syntax-highlighter` - Syntax highlighting for code blocks
- `remark-gfm` - GitHub Flavored Markdown plugin (tables, strikethrough, task lists, URLs)
  - Used in: `components/chat/markdown.tsx` for rendering AI responses

---

## Animation

- `framer-motion` - Production-ready animation library for React
  - Used in: `components/chat/message.tsx`, `multimodal-input.tsx`, `overview.tsx` for smooth UI transitions

---

## Layout & UI Utilities

- `react-resizable-panels` - Resizable split panel layouts
- `sonner` - Toast notification library
- `vaul` - Drawer/sidebar component

---

## React Hooks Utilities

- `usehooks-ts` - Collection of commonly used React hooks (useLocalStorage, useWindowSize, etc.)
  - Used in: `components/chat/multimodal-input.tsx` for local storage and window size detection

---

## AI Integration

- `ai` - Vercel AI SDK core package for calling AI models and handling streaming responses
- `@ai-sdk/react` - React hooks for AI SDK, provides `useChat` hook for managing chat state and API calls
  - Used in: `components/chat/chat.tsx`
- `@fingerprintjs/fingerprintjs` - Browser fingerprinting library for identifying unique visitors
  - Used in: `components/chat/chat.tsx` to generate client fingerprint for rate limiting

---

## Development & Tooling

- `concurrently` - Run multiple npm scripts in parallel
  - Used in `npm run dev` to simultaneously start Next.js and FastAPI

---

## Dev Dependencies

These are only used during development, not in production:

- `@types/node` - TypeScript type definitions for Node.js
- `@types/react` - TypeScript type definitions for React
- `@types/react-dom` - TypeScript type definitions for React DOM
- `postcss` - CSS post-processor (required by Tailwind)
- `tailwindcss` - Utility-first CSS framework
- `typescript` - TypeScript compiler

---

## When to Update Dependencies

1. **Check for updates** - `pnpm outdated`
2. **Review changes** - Check changelogs for breaking changes
3. **Update** - `pnpm update`
4. **Test** - `npm run test && npm run build`
5. **Audit** - `npm audit` to check for security vulnerabilities

---

## Key Points

- JSON doesn't support comments, so this file documents our reasoning
- Versions are locked in `pnpm-lock.yaml` for consistency
- Regular audits (`npm audit`) are more important than version pinning for security
- Always test after updating dependencies


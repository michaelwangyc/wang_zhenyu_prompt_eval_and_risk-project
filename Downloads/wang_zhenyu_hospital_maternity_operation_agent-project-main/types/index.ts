import { IconType } from "react-icons"
import { LucideIcon } from "lucide-react"

// ============================================================================
// Project Types
// ============================================================================

export interface Project {
  id: string
  title: string
  description: string
  status: string
  image: string
  href: string
  color: string
}

// ============================================================================
// Achievement Stats Types
// ============================================================================

export interface AchievementStat {
  number: string
  description: string
  color: string
  borderColor: string
  glowColor: string
  icon: IconType
  href: string
}

// ============================================================================
// Project Section Types (30 Voice AI Challenge)
// ============================================================================

export interface ProjectSection {
  id: string
  title: string
  description: string
  icon: LucideIcon
  content: string
}

// ============================================================================
// SEO Types
// ============================================================================

export interface SEOConfig {
  // 基础信息
  title: string
  description: string
  keywords?: string[]

  // URL 和站点信息
  url?: string
  siteName?: string

  // 图片
  image?: string
  imageWidth?: number
  imageHeight?: number
  imageAlt?: string

  // 作者和创建者
  author?: {
    name: string
    url: string
  }
  creator?: string

  // Open Graph 自定义
  ogTitle?: string
  ogDescription?: string

  // Twitter 自定义
  twitterTitle?: string
  twitterDescription?: string

  // 其他
  locale?: string
  type?: "website" | "article"

  // 索引控制
  noIndex?: boolean
  noFollow?: boolean
}

// ============================================================================
// Navigation Types
// ============================================================================

export interface NavItem {
  label: string
  href: string
}

export interface NavigationProps {
  items?: NavItem[]
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface MarkdownModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  content: string
  icon?: IconType
}

export interface SolutionCardProps {
  section: ProjectSection
  index: number
  onCardClick: (id: string) => void
}

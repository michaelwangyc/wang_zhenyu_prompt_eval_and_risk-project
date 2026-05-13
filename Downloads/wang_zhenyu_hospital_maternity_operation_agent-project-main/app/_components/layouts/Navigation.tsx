"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu, X, Github, HeartPulse } from "lucide-react"
import { NavItem, NavigationProps } from "@/types"
import { EXTERNAL_LINKS } from "@/lib/constants"

const DEFAULT_NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Chat", href: "/chat" },
]

export default function Navigation({ items = DEFAULT_NAV_ITEMS }: NavigationProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const pathname = usePathname()

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/"
    }
    return pathname.startsWith(href)
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#1D3557]/95 backdrop-blur-sm border-b-4 border-[#2A9D8F]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo / Brand */}
          <Link
            href="/"
            className="flex items-center gap-2.5 hover:opacity-90 transition-opacity"
          >
            <div className="w-9 h-9 bg-[#E63946] rounded-lg flex items-center justify-center border-2 border-[#C62B38] shadow-[2px_2px_0_rgba(198,43,56,0.5)]">
              <HeartPulse className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-display text-xl tracking-tight text-white">
              Materni<span className="text-[#2A9D8F]">Flow</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {items.map((item) => {
              const active = isActive(item.href)
              const isChat = item.href === "/chat"

              if (isChat) {
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="pixel-btn-teal !py-2 !px-5 !text-sm !rounded-lg !border-2 !shadow-[3px_3px_0] hover:!shadow-[4px_4px_0]"
                  >
                    Talk to AI
                  </Link>
                )
              }

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    font-display font-medium text-sm transition-colors cursor-pointer
                    ${active
                      ? "text-[#2A9D8F]"
                      : "text-white/80 hover:text-white"
                    }
                  `}
                >
                  {item.label}
                </Link>
              )
            })}

            <a
              href={EXTERNAL_LINKS.GITHUB_REPO}
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/70 hover:text-white transition-colors cursor-pointer"
              aria-label="View source on GitHub"
            >
              <Github size={20} strokeWidth={1.75} />
            </a>
          </div>

          {/* Mobile Navigation Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 text-white/80 hover:text-white transition-colors cursor-pointer"
              aria-label="Toggle menu"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t-2 border-[#2A9D8F]/40">
            <div className="py-4 space-y-2">
              {items.map((item) => {
                const active = isActive(item.href)
                const isChat = item.href === "/chat"

                if (isChat) {
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="block font-display font-semibold text-base py-3 px-4 bg-[#2A9D8F] text-white text-center rounded-xl mx-4 border-2 border-[#1E7A6E] shadow-[3px_3px_0_rgba(30,122,110,0.5)] cursor-pointer"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Talk to AI
                    </Link>
                  )
                }

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      block font-display font-medium text-base py-3 px-4 transition-colors cursor-pointer
                      ${active
                        ? "text-[#2A9D8F]"
                        : "text-white/80 hover:text-white"
                      }
                    `}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {item.label}
                  </Link>
                )
              })}

              <a
                href={EXTERNAL_LINKS.GITHUB_REPO}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 font-display font-medium text-base py-3 px-4 text-white/80 hover:text-white transition-colors cursor-pointer"
                onClick={() => setIsMenuOpen(false)}
                aria-label="View source on GitHub"
              >
                <Github size={20} strokeWidth={1.75} />
                <span>GitHub</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

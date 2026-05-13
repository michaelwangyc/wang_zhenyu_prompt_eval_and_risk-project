"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  ArrowRight,
  ArrowUpRight,
  Bed,
  HeartPulse,
  Baby,
  AlertTriangle,
  ClipboardList,
  Stethoscope,
} from "lucide-react"
import { EXTERNAL_LINKS } from "@/lib/constants"

export default function Hero() {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  const capabilities = [
    { icon: Bed, label: "Ward Status", color: "#2A9D8F" },
    { icon: Baby, label: "Patient Tracking", color: "#F4A261" },
    { icon: AlertTriangle, label: "High-Risk Alerts", color: "#E63946" },
    { icon: ClipboardList, label: "Order Management", color: "#2A9D8F" },
    { icon: Stethoscope, label: "Discharge Planning", color: "#1D3557" },
  ]

  const sourceLinks = [
    {
      emoji: "🔍",
      title: "Schema Extractor",
      description: "How the agent learns the database structure",
      href: EXTERNAL_LINKS.SOURCE_DB_SCHEMA_EXTRACTOR,
      path: "labor_ward_ai/db_schema/extractor.py",
    },
    {
      emoji: "📜",
      title: "Agent System Prompt",
      description: "The instruction set that drives reasoning & tool use",
      href: EXTERNAL_LINKS.SOURCE_AGENT_SYSTEM_PROMPT,
      path: "labor_ward_ai/prompts/bi-agent-system-prompt.md",
    },
    {
      emoji: "🛠️",
      title: "Agent Definition & Tools",
      description: "@tool methods — run SQL, fetch schema, write debug reports",
      href: EXTERNAL_LINKS.SOURCE_AGENT_DEFINITION,
      path: "labor_ward_ai/one/one_04_agent.py",
    },
    {
      emoji: "🔌",
      title: "UI Backend",
      description: "FastAPI route streaming Bedrock responses to the chat UI",
      href: EXTERNAL_LINKS.SOURCE_UI_BACKEND,
      path: "api/index.py",
    },
  ]

  const techStack = [
    {
      name: "AWS Bedrock",
      href: "https://aws.amazon.com/bedrock/",
      className:
        "bg-[#FF9900]/15 text-[#B26500] dark:text-[#FFB84D] border-[#FF9900]/50 hover:bg-[#FF9900]/25",
    },
    {
      name: "Strands-Agents",
      href: "https://strandsagents.com/",
      className:
        "bg-[#2A9D8F]/15 text-[#1E7A6E] dark:text-[#5CC0B5] border-[#2A9D8F]/50 hover:bg-[#2A9D8F]/25",
    },
    {
      name: "PostgreSQL",
      href: "https://www.postgresql.org/",
      className:
        "bg-[#336791]/12 text-[#336791] dark:text-[#6FA4D0] border-[#336791]/45 hover:bg-[#336791]/20",
    },
    {
      name: "Next.js",
      href: "https://nextjs.org/",
      className:
        "bg-[#1D3557]/10 text-[#1D3557] dark:bg-white/10 dark:text-white border-[#1D3557]/35 dark:border-white/35 hover:bg-[#1D3557]/18 dark:hover:bg-white/20",
    },
    {
      name: "AI-SDK",
      href: "https://ai-sdk.dev/docs/introduction",
      className:
        "bg-violet-600/12 text-violet-800 dark:text-violet-300 border-violet-700/40 hover:bg-violet-600/18",
    },
  ]

  return (
    <section className="relative min-h-screen flex flex-col justify-center pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-hospital-floor overflow-hidden">
      {/* Decorative pixel cross — top right */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-8 -right-8 sm:right-8 w-[200px] h-[200px] opacity-[0.08] dark:opacity-[0.05]"
      >
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <rect x="35" y="5" width="30" height="90" rx="3" fill="#E63946" />
          <rect x="5" y="35" width="90" height="30" rx="3" fill="#E63946" />
        </svg>
      </div>

      {/* Decorative heartbeat line — bottom left */}
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-12 -left-16 w-[400px] h-[60px] opacity-[0.10] dark:opacity-[0.06]"
      >
        <svg viewBox="0 0 400 60" className="w-full h-full">
          <polyline
            fill="none"
            stroke="#2A9D8F"
            strokeWidth="3"
            points="0,30 80,30 100,30 120,10 140,50 160,20 180,40 200,30 400,30"
          />
        </svg>
      </div>

      <div className="max-w-4xl mx-auto w-full relative">
        {/* Title */}
        <div
          className={`transition-all duration-700 delay-100 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-8"}`}
        >
          {/* Pixel badge */}
          <div className="inline-flex items-center gap-2 mb-5 px-4 py-1.5 bg-[#E63946] text-white rounded-lg border-2 border-[#C62B38] shadow-[3px_3px_0_rgba(198,43,56,0.4)] font-pixel text-lg">
            <HeartPulse className="w-5 h-5" strokeWidth={2.5} />
            AI-Powered OB/GYN Assistant
          </div>

          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[1.05] mb-4 tracking-tight">
            <span className="text-[#1D3557] dark:text-white">Materni</span>
            <span className="text-[#2A9D8F]">Flow</span>
          </h1>

          <p className="text-base sm:text-lg text-[#1D3557]/70 dark:text-white/70 mb-4 max-w-2xl font-body">
            An AI assistant designed for OB/GYN nurses. Query real-time ward status, predict patient length-of-stay, coordinate room assignments, receive high-risk alerts, and place orders — all through natural conversation.
          </p>

          <div className="flex gap-1.5 mb-10">
            <div className="w-8 h-2 bg-[#2A9D8F] rounded-full" />
            <div className="w-4 h-2 bg-[#F4A261] rounded-full" />
            <div className="w-2 h-2 bg-[#E63946] rounded-full" />
          </div>
        </div>

        {/* Architecture note */}
        <div
          className={`transition-all duration-700 delay-200 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <div className="mb-10 p-4 bg-[#E8F5F0]/80 dark:bg-[#1A3A3A]/60 border-2 border-[#2A9D8F]/30 dark:border-[#2A9D8F]/40 rounded-xl border-l-4 border-l-[#2A9D8F]">
            <p className="text-sm text-[#1D3557]/80 dark:text-white/80 font-body leading-relaxed">
              <span className="font-pixel text-base text-[#2A9D8F] mr-1">ARCH:</span>
              AI Agent has read-only database access. All write operations go through independent Lambda functions with business validation — the AI can see and speak, but actions are verified before execution.
            </p>
          </div>
        </div>

        {/* Capability Cards */}
        <div
          className={`transition-all duration-700 delay-300 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-10">
            {capabilities.map((cap, index) => (
              <div
                key={cap.label}
                className={`relative p-5 rounded-xl bg-white/90 dark:bg-[#1A3A3A]/70 border-2 border-[#2A9D8F]/25 dark:border-[#2A9D8F]/30 shadow-[3px_3px_0_rgba(42,157,143,0.15)] hover:shadow-[4px_4px_0_rgba(42,157,143,0.25)] hover:translate-x-[-1px] hover:translate-y-[-1px] transition-all duration-200 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
                style={{ transitionDelay: `${400 + index * 100}ms` }}
              >
                <cap.icon
                  className="w-7 h-7 mb-3"
                  strokeWidth={2}
                  style={{ color: cap.color }}
                />
                <p className="text-sm font-display font-medium text-[#1D3557] dark:text-white">
                  {cap.label}
                </p>
              </div>
            ))}
          </div>

          {/* Tech Stack Tags */}
          <div className="flex flex-wrap gap-2.5 mb-10">
            {techStack.map((tech) => (
              <a
                key={tech.name}
                href={tech.href}
                target="_blank"
                rel="noopener noreferrer"
                className={`font-pixel text-base px-4 py-1.5 rounded-lg border-2 transition-colors ${tech.className}`}
              >
                {tech.name}
              </a>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div
          className={`transition-all duration-700 delay-500 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <Link
            href="/chat"
            className="group flex items-center justify-between w-full p-6 bg-white/90 dark:bg-[#1A3A3A]/70 border-3 border-[#2A9D8F] rounded-2xl shadow-[4px_4px_0_rgba(30,122,110,0.4)] hover:shadow-[6px_6px_0_rgba(30,122,110,0.4)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all duration-200 cursor-pointer"
            style={{ borderWidth: '3px' }}
          >
            <div>
              <h3 className="font-display text-2xl sm:text-3xl text-[#1D3557] dark:text-white mb-1">
                Talk to{" "}
                <span className="text-[#2A9D8F]">
                  MaterniFlow
                </span>
              </h3>
              <p className="text-[#1D3557]/60 dark:text-white/60 text-sm sm:text-base font-body">
                Experience the AI scheduling assistant in action
              </p>
            </div>
            <div className="flex items-center justify-center w-14 h-14 rounded-xl bg-[#2A9D8F] border-2 border-[#1E7A6E] shadow-[2px_2px_0_rgba(30,122,110,0.5)] group-hover:shadow-[3px_3px_0_rgba(30,122,110,0.5)] group-hover:translate-x-[-1px] group-hover:translate-y-[-1px] transition-all">
              <ArrowRight className="w-6 h-6 text-white group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>
        </div>

        {/* Under the Hood */}
        <div
          className={`mt-16 transition-all duration-700 delay-[600ms] ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <div className="mb-6">
            <h3 className="font-display text-2xl sm:text-3xl tracking-tight mb-2 text-[#1D3557] dark:text-white">
              Under the{" "}
              <span className="text-[#2A9D8F]">Hood</span>
            </h3>
            <div className="flex gap-1 mb-3">
              <div className="w-12 h-1.5 bg-[#2A9D8F] rounded-full" />
              <div className="w-3 h-1.5 bg-[#F4A261] rounded-full" />
            </div>
            <p className="text-sm sm:text-base text-[#1D3557]/60 dark:text-white/60 max-w-2xl font-body">
              Here&apos;s how the agent actually works under the hood.
              Each link points to the production source on GitHub.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            {sourceLinks.map((link, index) => (
              <a
                key={link.href}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className={`group flex items-center gap-4 p-4 sm:p-5 bg-white/90 dark:bg-[#1A3A3A]/60 border-2 border-[#2A9D8F]/20 dark:border-[#2A9D8F]/30 rounded-xl shadow-[2px_2px_0_rgba(42,157,143,0.12)] hover:shadow-[4px_4px_0_rgba(42,157,143,0.2)] hover:border-[#2A9D8F]/50 hover:translate-x-[-1px] hover:translate-y-[-1px] transition-all duration-200 cursor-pointer ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
                style={{ transitionDelay: `${700 + index * 80}ms` }}
              >
                {/* Emoji badge */}
                <div className="flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 shrink-0 rounded-xl bg-[#E8F5F0] dark:bg-[#0F2027] border-2 border-[#2A9D8F]/25 dark:border-[#2A9D8F]/30 text-2xl sm:text-3xl">
                  <span aria-hidden>{link.emoji}</span>
                </div>

                {/* Title + description + path */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-display text-base sm:text-lg font-semibold text-[#1D3557] dark:text-white leading-tight">
                    {link.title}
                  </h4>
                  <p className="text-sm text-[#1D3557]/60 dark:text-white/60 mt-0.5 leading-snug font-body">
                    {link.description}
                  </p>
                  <p className="font-pixel text-sm text-[#2A9D8F]/70 dark:text-[#5CC0B5]/70 mt-1 truncate">
                    {link.path}
                  </p>
                </div>

                {/* Arrow */}
                <div className="flex items-center justify-center w-9 h-9 shrink-0 rounded-lg bg-[#2A9D8F]/10 dark:bg-[#2A9D8F]/20 group-hover:bg-[#2A9D8F] transition-colors">
                  <ArrowUpRight
                    className="w-4 h-4 text-[#2A9D8F] group-hover:text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all"
                    strokeWidth={2}
                  />
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Database Info */}
        <div
          className={`mt-10 transition-all duration-700 delay-[1100ms] ${isVisible ? "opacity-100" : "opacity-0"}`}
        >
          <div className="p-4 bg-[#F4A261]/10 dark:bg-[#F4A261]/5 border-2 border-[#F4A261]/25 rounded-xl border-l-4 border-l-[#F4A261]">
            <p className="text-sm text-[#1D3557]/70 dark:text-white/70 font-body">
              <span className="font-pixel text-base text-[#F4A261] mr-1">DATA:</span>
              Built with Strands Agents SDK + AWS Lambda + PostgreSQL + Next.js. This demo is a personal recreation of a POC originally developed during an internship for a healthcare client exploring AI integration. Further client engagement was led by the senior tech lead and account manager.
            </p>
            <p className="mt-2 text-xs text-[#1D3557]/50 dark:text-white/50 font-body">
              All data in this demo is derived from legacy records that have been fully de-identified and modified — no sensitive information, no PII, and no production patient data is included.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

"use client"

import Hero from "./_components/Hero"
import { HeartPulse } from "lucide-react"

export default function HomePageContent() {
  return (
    <div className="min-h-screen bg-[#FDF6EC] dark:bg-[#0F2027] text-[#1D3557] dark:text-white font-body">
      <div className="relative">
        <Hero />

        <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t-4 border-[#2A9D8F] bg-[#1D3557] dark:bg-[#0A1520]">
          <div className="max-w-7xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <HeartPulse className="w-4 h-4 text-[#E63946]" strokeWidth={2.5} />
              <span className="font-pixel text-lg text-[#2A9D8F]">MaterniFlow</span>
            </div>
            <p className="text-sm text-white/70 font-body">
              &copy; {new Date().getFullYear()}{" "}
              <span className="text-white/90">Michael Wang</span>
              <span className="mx-2 text-[#2A9D8F]">&bull;</span>
              <span className="font-pixel text-base">MIT licensed</span>
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}

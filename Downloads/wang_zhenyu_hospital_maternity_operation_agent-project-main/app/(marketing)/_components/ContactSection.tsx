"use client"

import { Mail } from "lucide-react"
import { FaLinkedin } from "react-icons/fa"

export default function ContactSection() {
  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8 border-t-4 border-black dark:border-white">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <h2 className="font-display text-display-md text-black dark:text-white mb-8">
          LET'S CONNECT
        </h2>

        <p className="text-lg text-gray-600 dark:text-gray-400 mb-12 max-w-xl">
          Ready to collaborate or discuss opportunities? Reach out and let's build something great together.
        </p>

        {/* Action Buttons - Bold Style */}
        <div className="flex flex-col sm:flex-row gap-4">
          <a
            href="mailto:about@michaelwangyc.me"
            className="bold-button-accent flex items-center justify-center gap-3"
          >
            <Mail size={20} />
            SEND EMAIL
          </a>
          <a
            href="https://example.com"
            target="_blank"
            rel="noopener noreferrer"
            className="bold-button flex items-center justify-center gap-3"
          >
            <FaLinkedin size={20} />
            LINKEDIN
          </a>
        </div>
      </div>
    </section>
  )
}

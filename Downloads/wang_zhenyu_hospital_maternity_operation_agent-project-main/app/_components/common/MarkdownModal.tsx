"use client"

import { useEffect } from "react"
import { X } from "lucide-react"
import MarkdownRenderer from "@/components/ui/markdown-renderer"
import { MarkdownModalProps } from "@/types"

export default function MarkdownModal({
  isOpen,
  onClose,
  title,
  description,
  content,
  icon: Icon,
}: MarkdownModalProps) {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div className="relative bg-regular-button/95 backdrop-blur-md border border-primary/30 rounded-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden shadow-2xl shadow-primary/20">
        {/* Modal Header */}
        <div className="flex items-start justify-between p-6 border-b border-primary/20">
          <div className="flex items-start gap-4">
            {Icon && (
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-primary/20 rounded-xl flex items-center justify-center">
                  <Icon size={24} className="text-primary" />
                </div>
              </div>
            )}
            <div>
              <h2 className="text-2xl font-bold text-primary mb-2">
                {title}
              </h2>
              {description && (
                <p className="text-text-secondary">
                  {description}
                </p>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-text-secondary hover:text-primary transition-colors duration-200 p-2 hover:bg-primary/10 rounded-lg"
            aria-label="Close modal"
          >
            <X size={24} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="overflow-y-auto max-h-[60vh] p-6">
          <MarkdownRenderer content={content} />
        </div>
      </div>
    </div>
  )
}

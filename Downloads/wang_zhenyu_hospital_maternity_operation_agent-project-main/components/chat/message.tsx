"use client";

import type { UIMessage } from "ai";
import { motion } from "framer-motion";
import Image from "next/image";
import { useState } from "react";

import { Markdown } from "./markdown";
import { cn } from "@/lib/utils";
import { CDN_ASSETS } from "@/lib/constants";

/**
 * Collapsible component for displaying reasoning/thinking content.
 * Shows a summary by default, expands to show full content on click.
 */
const ReasoningBlock = ({ text }: { text: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Truncate text for preview (first 100 chars)
  const previewText = text.length > 100 ? text.slice(0, 100) + "..." : text;

  return (
    <div className="border border-amber-200 dark:border-amber-800 rounded-lg bg-amber-50 dark:bg-amber-950/30 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center gap-2 text-left hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
      >
        <svg
          className={cn(
            "w-4 h-4 text-amber-600 dark:text-amber-400 transition-transform",
            isExpanded && "rotate-90"
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
          Thinking
        </span>
        {!isExpanded && (
          <span className="text-xs text-amber-600 dark:text-amber-400 truncate flex-1">
            {previewText}
          </span>
        )}
      </button>
      {isExpanded && (
        <div className="px-3 py-2 border-t border-amber-200 dark:border-amber-800">
          <div className="text-xs text-amber-800 dark:text-amber-200 whitespace-pre-wrap">
            {text}
          </div>
        </div>
      )}
    </div>
  );
};

export const PreviewMessage = ({
  message,
  append,
}: {
  chatId: string;
  message: UIMessage;
  isLoading: boolean;
  append?: (message: any) => Promise<string | null | undefined>;
}) => {
  return (
    <motion.div
      className="w-full mx-auto max-w-3xl group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      <div
        className={cn(
          "flex gap-3 w-full",
          message.role === "user" ? "justify-end" : "justify-start"
        )}
      >
        {/* AI Assistant Avatar - Left side */}
        {message.role === "assistant" && (
          <div className="stamped w-8 h-8 flex items-center justify-center bg-[#003A5F] dark:bg-[#0A1F35] border border-[#003A5F]/40 dark:border-[#F5F0E1]/15 shrink-0 rounded-lg">
            <span className="font-serif italic text-xs text-[#F5F0E1]">AI</span>
          </div>
        )}

        <div
          className={cn(
            "stamped flex flex-col gap-2 max-w-[85%] sm:max-w-[75%] p-4 rounded-xl border",
            message.role === "user"
              ? "bg-[#003A5F] dark:bg-[#0A1F35] border-[#003A5F]/40 dark:border-[#F5F0E1]/15 text-[#F5F0E1]"
              : "bg-[#FAF6E9]/85 dark:bg-[#0F2741]/75 border-[#003A5F]/15 dark:border-[#F5F0E1]/12"
          )}
        >
          {/* AI SDK v5: Use parts instead of content */}
          {message.parts && message.parts.length > 0 && (
            <div className="flex flex-col gap-4">
              {message.parts.map((part: any, index: number) => {
                // Render reasoning/thinking content
                if (part.type === 'reasoning' && part.text) {
                  return (
                    <ReasoningBlock key={index} text={part.text} />
                  );
                }
                // Render text content
                if (part.type === 'text' && part.text) {
                  return (
                    <div
                      key={index}
                      className={cn(
                        message.role === "assistant"
                          ? "text-[#1A1A1A]/90 dark:text-[#F5F0E1]/90"
                          : "text-[#F5F0E1]"
                      )}
                    >
                      <Markdown
                        variant="chat"
                        onQuestionClick={(question) => {
                          append?.({
                            role: 'user',
                            content: question,
                          });
                        }}
                      >
                        {part.text}
                      </Markdown>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          )}
        </div>

        {/* User Avatar - Right side */}
        {message.role === "user" && (
          <div className="stamped w-8 h-8 overflow-hidden border border-[#003A5F]/30 dark:border-[#F5F0E1]/15 shrink-0 rounded-lg">
            <Image
              src={CDN_ASSETS.PROFILE_PHOTO}
              alt="User Profile"
              width={32}
              height={32}
              className="w-full h-full object-cover"
            />
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const ThinkingMessage = () => {
  const role = "assistant";

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div className="flex gap-3 w-full justify-start">
        <div className="stamped w-8 h-8 flex items-center justify-center bg-[#003A5F] dark:bg-[#0A1F35] border border-[#003A5F]/40 dark:border-[#F5F0E1]/15 shrink-0 rounded-lg">
          <span className="font-serif italic text-xs text-[#F5F0E1]">AI</span>
        </div>

        <div className="stamped p-4 bg-[#FAF6E9]/85 dark:bg-[#0F2741]/75 border border-[#003A5F]/15 dark:border-[#F5F0E1]/12 rounded-xl">
          <div className="flex items-center gap-2 text-[#7A6F5F] dark:text-[#B8A887]">
            <span className="inline-block w-2 h-2 bg-[#D03027] dark:bg-[#E8564E] rounded-full animate-pulse" />
            <span className="font-serif italic text-sm">Thinking...</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

"use client";

import type { ChatRequestOptions, UIMessage } from "ai";
import { motion } from "framer-motion";
import type React from "react";
import {
  useRef,
  useEffect,
  useCallback,
  type Dispatch,
  type SetStateAction,
} from "react";
import { toast } from "sonner";
import { useLocalStorage, useWindowSize } from "usehooks-ts";

import { cn, sanitizeUIMessages } from "@/lib/utils";

import { ArrowUpIcon, StopIcon } from "./icons";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import suggestedActionsData from "@/data/suggested-actions.json";

const suggestedActions = suggestedActionsData;

export function MultimodalInput({
  chatId,
  input,
  setInput,
  isLoading,
  stop,
  messages,
  setMessages,
  append,
  handleSubmit,
  className,
}: {
  chatId: string;
  input: string;
  setInput: (value: string) => void;
  isLoading: boolean;
  stop: () => void;
  messages: Array<UIMessage>;
  setMessages: Dispatch<SetStateAction<Array<UIMessage>>>;
  append: (
    message: any,
    chatRequestOptions?: ChatRequestOptions,
  ) => Promise<string | null | undefined>;
  handleSubmit: (
    event?: {
      preventDefault?: () => void;
    },
    chatRequestOptions?: ChatRequestOptions,
  ) => void;
  className?: string;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { width } = useWindowSize();

  useEffect(() => {
    if (textareaRef.current) {
      adjustHeight();
    }
  }, []);

  const adjustHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight + 2}px`;
    }
  };

  const [localStorageInput, setLocalStorageInput] = useLocalStorage(
    "input",
    "",
  );

  useEffect(() => {
    if (textareaRef.current) {
      const domValue = textareaRef.current.value;
      const finalValue = domValue || localStorageInput || "";
      setInput(finalValue);
      adjustHeight();
    }
  }, []);

  useEffect(() => {
    setLocalStorageInput(input);
  }, [input, setLocalStorageInput]);

  const handleInput = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(event.target.value);
    adjustHeight();
  };

  const submitForm = useCallback(() => {
    handleSubmit(undefined, {});
    setLocalStorageInput("");

    if (width && width > 768) {
      textareaRef.current?.focus();
    }
  }, [handleSubmit, setLocalStorageInput, width]);

  return (
    <div className="relative w-full flex flex-col gap-3">
      {/* Suggested Questions */}
      {messages.length === 0 && (
        <div className="flex flex-col gap-3">
          <div className="border-2 border-[#2A9D8F]/25 dark:border-[#2A9D8F]/30 p-3 bg-[#E8F5F0]/60 dark:bg-[#1A3A3A]/50 rounded-xl shadow-[2px_2px_0_rgba(42,157,143,0.08)]">
            <p className="font-pixel text-base text-[#2A9D8F] text-center">
              Ask me directly or click a suggestion
            </p>
          </div>

          <div className="max-h-[320px] sm:max-h-[280px] overflow-y-auto">
            <div className="grid sm:grid-cols-2 gap-2 w-full pr-1">
              {suggestedActions.map((suggestedAction, index) => (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  transition={{ delay: 0.05 * index }}
                  key={`suggested-action-${suggestedAction.title}-${index}`}
                >
                  <Button
                    variant="ghost"
                    onClick={async () => {
                      append({
                        role: "user",
                        content: suggestedAction.action,
                      });
                    }}
                    className="group text-left border-2 border-[#2A9D8F]/20 dark:border-[#2A9D8F]/25 bg-white/80 dark:bg-[#1A3A3A]/50 hover:bg-[#E8F5F0] dark:hover:bg-[#1A3A3A]/70 hover:border-[#2A9D8F]/50 px-4 py-3 text-sm flex-1 gap-1 sm:flex-col w-full h-auto justify-start items-start shadow-[2px_2px_0_rgba(42,157,143,0.08)] hover:shadow-[3px_3px_0_rgba(42,157,143,0.15)] hover:translate-x-[-1px] hover:translate-y-[-1px] transition-all cursor-pointer rounded-xl"
                  >
                    <span className="font-display text-sm text-[#1D3557] dark:text-white">
                      {suggestedAction.title}
                    </span>
                    <span className="font-pixel text-sm text-[#2A9D8F] group-hover:text-[#1E7A6E] dark:group-hover:text-[#5CC0B5] leading-snug transition-colors">
                      {suggestedAction.label}
                    </span>
                  </Button>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* User Message Input Form */}
      <div className="relative">
        <Textarea
          ref={textareaRef}
          placeholder="Ask about ward status, patients, schedules..."
          value={input}
          onChange={handleInput}
          className={cn(
            "min-h-[24px] max-h-[calc(75dvh)] overflow-hidden resize-none !text-base font-body",
            "bg-white/90 dark:bg-[#1A3A3A]/60 border-2 border-[#2A9D8F]/30 dark:border-[#2A9D8F]/35 rounded-xl",
            "focus:border-[#2A9D8F] dark:focus:border-[#5CC0B5] focus:ring-[#2A9D8F]/25 dark:focus:ring-[#5CC0B5]/25 focus:ring-2",
            "text-[#1D3557] dark:text-white placeholder:text-[#1D3557]/40 dark:placeholder:text-white/40",
            "shadow-[2px_2px_0_rgba(42,157,143,0.1)]",
            "pr-12",
            className,
          )}
          rows={3}
          autoFocus
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();

              if (isLoading) {
                toast.error("Please wait for the response to complete!");
              } else {
                submitForm();
              }
            }
          }}
        />

        {isLoading ? (
          <Button
            className="p-2 h-fit absolute bottom-2 right-2 bg-white dark:bg-[#1A3A3A] border-2 border-[#E63946]/40 dark:border-[#E63946]/50 hover:bg-[#FFF0F0] dark:hover:bg-[#3A1A1A] text-[#E63946] cursor-pointer rounded-lg shadow-[2px_2px_0_rgba(230,57,70,0.15)]"
            onClick={(event) => {
              event.preventDefault();
              stop();
              setMessages((messages) => sanitizeUIMessages(messages));
            }}
          >
            <StopIcon size={16} />
          </Button>
        ) : (
          <Button
            className="p-2 h-fit absolute bottom-2 right-2 bg-[#2A9D8F] hover:bg-[#1E7A6E] dark:bg-[#2A9D8F] dark:hover:bg-[#1E7A6E] text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer rounded-lg border-2 border-[#1E7A6E] shadow-[2px_2px_0_rgba(30,122,110,0.4)] hover:shadow-[3px_3px_0_rgba(30,122,110,0.4)]"
            onClick={(event) => {
              event.preventDefault();
              submitForm();
            }}
            disabled={input.length === 0}
          >
            <ArrowUpIcon size={16} />
          </Button>
        )}
      </div>
    </div>
  );
}

'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface MarkdownProps {
  children: string;
  variant?: 'chat' | 'card';
  onQuestionClick?: (question: string) => void;
}

export const Markdown = ({ children, variant = 'chat', onQuestionClick }: MarkdownProps) => {
  // Preprocess markdown to handle #ask: links with spaces
  const preprocessedChildren = children.replace(
    /\[([^\]]+)\]\(#ask:([^)]+)\)/g,
    '[$1](<#ask:$2>)'
  );

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
          a: ({ href, children }) => {
            // Handle clickable question links
            if (href?.startsWith('#ask:')) {
              const question = decodeURIComponent(href.replace('#ask:', ''));
              return (
                <button
                  onClick={() => onQuestionClick?.(question)}
                  className="text-[#D03027] dark:text-[#E8564E] hover:text-[#A8261F] dark:hover:text-[#D03027] underline font-medium cursor-pointer transition-colors"
                >
                  {children}
                </button>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#D03027] dark:text-[#E8564E] hover:text-[#A8261F] dark:hover:text-[#D03027] underline"
              >
                {children}
              </a>
            );
          },
          code: ({ className, children, ...props }) => {
            // Inline code doesn't have a className (language-*), code blocks do
            const isInline = !className;
            if (isInline) {
              return (
                <code className="bg-[#F5F0E1]/60 dark:bg-[#0A1F35]/60 border border-[#003A5F]/15 dark:border-[#F5F0E1]/12 px-1.5 py-0.5 rounded text-sm font-mono text-[#003A5F] dark:text-[#F5F0E1]">
                  {children}
                </code>
              );
            }
            return (
              <code className={cn("block bg-[#F5F0E1]/60 dark:bg-[#0A1F35]/60 border border-[#003A5F]/15 dark:border-[#F5F0E1]/12 p-3 rounded-lg my-3 overflow-x-auto text-sm font-mono text-[#003A5F] dark:text-[#F5F0E1]", className)}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="bg-[#F5F0E1]/60 dark:bg-[#0A1F35]/60 border border-[#003A5F]/15 dark:border-[#F5F0E1]/12 p-4 rounded-lg my-3 overflow-x-auto">
              {children}
            </pre>
          ),
          ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-[#003A5F] dark:text-[#F5F0E1]">{children}</strong>,
          em: ({ children }) => <em className="font-serif italic text-[#7A6F5F] dark:text-[#B8A887]">{children}</em>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-[#D03027] dark:border-[#E8564E] pl-4 my-3 text-[#7A6F5F] dark:text-[#B8A887] italic bg-[#F5F0E1]/50 dark:bg-[#0A1F35]/50 py-2 rounded-r">
              {children}
            </blockquote>
          ),
          h1: ({ children }) => <h1 className="font-display text-2xl font-semibold mb-3 mt-4 text-[#003A5F] dark:text-[#F5F0E1]">{children}</h1>,
          h2: ({ children }) => <h2 className="font-display text-xl font-semibold mb-3 mt-4 text-[#003A5F] dark:text-[#F5F0E1]">{children}</h2>,
          h3: ({ children }) => <h3 className="font-display text-lg font-semibold mb-2 mt-3 text-[#003A5F] dark:text-[#F5F0E1]">{children}</h3>,
          h4: ({ children }) => <h4 className="font-display text-base font-semibold mb-2 mt-3 text-[#003A5F] dark:text-[#F5F0E1]">{children}</h4>,
          table: ({ children }) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border border-[#003A5F]/15 dark:border-[#F5F0E1]/12 rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-[#F5F0E1]/60 dark:bg-[#0A1F35]/60">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left text-sm font-display font-semibold text-[#003A5F] dark:text-[#F5F0E1] border-b border-[#003A5F]/15 dark:border-[#F5F0E1]/12">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2 text-sm border-b border-[#003A5F]/15 dark:border-[#F5F0E1]/12">
              {children}
            </td>
          ),
        }}
      >
        {preprocessedChildren}
      </ReactMarkdown>
    </div>
  );
};

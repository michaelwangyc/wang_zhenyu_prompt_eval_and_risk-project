"use client"

import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Components } from 'react-markdown'
import type { ReactElement } from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export default function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  const components: Components = {
    // Headers
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-primary mb-4 mt-6 first:mt-0">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-bold text-primary mb-4 mt-8 first:mt-0">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-primary mb-3 mt-6 first:mt-0">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-primary mb-2 mt-4">
        {children}
      </h4>
    ),
    
    // Paragraphs
    p: ({ children }) => (
      <p className="text-text-secondary leading-relaxed mb-4">
        {children}
      </p>
    ),
    
    // Strong (Bold)
    strong: ({ children }) => (
      <strong className="font-semibold text-text-primary">
        {children}
      </strong>
    ),
    
    // Emphasis (Italic)
    em: ({ children }) => (
      <em className="italic text-text-secondary">
        {children}
      </em>
    ),
    
    // Links
    a: ({ href, children }) => (
      <a 
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary hover:text-highlight underline decoration-primary/50 hover:decoration-highlight/80 transition-colors duration-200"
      >
        {children}
      </a>
    ),
    
    // Images
    img: ({ src, alt }) => (
      <img 
        src={src} 
        alt={alt} 
        className="max-w-full h-auto rounded-lg border border-primary/20 my-4"
      />
    ),
    
    // Unordered Lists
    ul: ({ children }) => (
      <ul className="list-disc list-inside space-y-1 mb-4 ml-4 text-text-secondary">
        {children}
      </ul>
    ),
    
    // Ordered Lists
    ol: ({ children }) => (
      <ol className="list-decimal list-inside space-y-1 mb-4 ml-4 text-text-secondary">
        {children}
      </ol>
    ),
    
    // List Items
    li: ({ children }) => (
      <li className="mb-1">
        {children}
      </li>
    ),
    
    // Blockquotes
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-secondary/50 bg-secondary/5 pl-4 py-2 mb-4 italic text-text-secondary">
        {children}
      </blockquote>
    ),
    
    // Inline Code
    code: ({ children, className }) => {
      // Check if this is a code block (has language class) or inline code
      const match = /language-(\w+)/.exec(className || '')
      
      if (!match) {
        // Inline code
        return (
          <code className="bg-primary/10 text-primary px-2 py-1 rounded text-sm font-mono">
            {children}
          </code>
        )
      }
      
      // This shouldn't happen as code blocks are handled by the `pre` component
      return <code>{children}</code>
    },
    
    // Code Blocks
    pre: ({ children, ...props }) => {
      // Extract the code element
      const codeElement = children as ReactElement
      if (codeElement?.props?.className) {
        const match = /language-(\w+)/.exec(codeElement.props.className || '')
        const language = match ? match[1] : 'text'
        
        return (
          <div className="mb-4">
            <SyntaxHighlighter
              style={oneDark}
              language={language}
              customStyle={{
                margin: 0,
                borderRadius: '8px',
                fontSize: '14px',
                padding: '16px',
              }}
              codeTagProps={{
                style: {
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                }
              }}
            >
              {String(codeElement.props.children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          </div>
        )
      }
      
      // Fallback for code blocks without language
      return (
        <pre className="bg-primary/10 text-text-primary p-4 rounded-lg mb-4 overflow-x-auto text-sm font-mono">
          {children}
        </pre>
      )
    },
    
    // Horizontal Rule
    hr: () => (
      <hr className="border-primary/20 my-6" />
    ),
  }

  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      <ReactMarkdown components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
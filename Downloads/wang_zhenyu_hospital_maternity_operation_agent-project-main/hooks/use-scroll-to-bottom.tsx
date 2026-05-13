import { useEffect, useRef, type RefObject } from "react";

/**
 * Custom hook for automatic scrolling to bottom of a container
 *
 * This hook provides two refs:
 * 1. containerRef: Attach to the scrollable container
 * 2. endRef: Attach to an anchor element at the bottom
 *
 * The hook uses MutationObserver to detect DOM changes and automatically
 * scrolls to the bottom, ensuring users always see the latest content.
 *
 * Uses smooth scrolling for better UX.
 */
export function useScrollToBottom<T extends HTMLElement>(): [
  RefObject<T>,
  RefObject<T>,
] {
  const containerRef = useRef<T>(null);
  const endRef = useRef<T>(null);

  useEffect(() => {
    const container = containerRef.current;
    const end = endRef.current;

    if (container && end) {
      // Use MutationObserver to detect DOM changes in the container
      const observer = new MutationObserver(() => {
        // Scroll to bottom with smooth animation
        end.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });

      // Only observe child additions (new messages), not text changes
      // This prevents scrolling while user is typing or during streaming updates
      observer.observe(container, {
        childList: true,      // Watch for added/removed children (new messages only)
        subtree: false,       // Don't watch nested elements (prevents excessive triggers)
        // Note: attributes and characterData are intentionally disabled
        // to prevent scrolling during typing or text updates
      });

      return () => observer.disconnect();
    }
  }, []);

  return [containerRef, endRef];
}

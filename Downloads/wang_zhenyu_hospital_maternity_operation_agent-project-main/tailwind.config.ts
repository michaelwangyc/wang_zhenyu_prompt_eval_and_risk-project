import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme Hospital Color System
        primary: {
          DEFAULT: "#2A9D8F", // hospital teal
          foreground: "#FFFFFF",
          light: "#5CC0B5",
          dark: "#1E7A6E",
        },
        secondary: {
          DEFAULT: "#1D3557", // scrubs navy
          foreground: "#FFFFFF",
        },
        accent: {
          DEFAULT: "#F4A261", // pill orange
          foreground: "#1D3557",
          light: "#F7BC85",
          dark: "#E08C3B",
        },
        background: {
          DEFAULT: "#FDF6EC",
          dark: "#0F2027",
        },
        surface: {
          DEFAULT: "#E8F5F0",
          dark: "#1A3A3A",
        },
        muted: {
          DEFAULT: "#F5E6CC",
          foreground: "#6B7C8D",
          dark: "#1A3A3A",
        },
        border: {
          DEFAULT: "#B8DDD6",
          dark: "#2A5050",
        },
        // Hospital specific
        "hospital-teal": "#2A9D8F",
        "cross-red": "#E63946",
        "clipboard-brown": "#8B6914",
        "floor-cream": "#FDF6EC",
        "scrubs-navy": "#1D3557",
        "pill-orange": "#F4A261",
        // shadcn/ui compatibility
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        foreground: "hsl(var(--foreground))",
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        display: ["var(--font-fredoka)", "sans-serif"],
        body: ["var(--font-nunito)", "sans-serif"],
        heading: ["var(--font-fredoka)", "sans-serif"],
        pixel: ["var(--font-vt323)", "monospace"],
        serif: ["Georgia", "serif"],
      },
      fontSize: {
        "display-xl": ["clamp(4rem, 15vw, 12rem)", { lineHeight: "0.9", letterSpacing: "-0.02em" }],
        "display-lg": ["clamp(3rem, 10vw, 8rem)", { lineHeight: "0.95", letterSpacing: "-0.02em" }],
        "display-md": ["clamp(2rem, 6vw, 4rem)", { lineHeight: "1", letterSpacing: "-0.01em" }],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-in-left": "slideInLeft 0.6s ease-out",
        "slide-in-right": "slideInRight 0.6s ease-out",
        "bounce-gentle": "bounceGentle 1s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideInLeft: {
          "0%": { transform: "translateX(-30px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        slideInRight: {
          "0%": { transform: "translateX(30px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        bounceGentle: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-4px)" },
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        none: "0px",
      },
      boxShadow: {
        "hospital": "4px 4px 0 rgba(30, 122, 110, 0.4)",
        "hospital-lg": "6px 6px 0 rgba(30, 122, 110, 0.4)",
        "hospital-card": "3px 3px 0 rgba(42, 157, 143, 0.3), inset 0 1px 0 rgba(255,255,255,0.8)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config

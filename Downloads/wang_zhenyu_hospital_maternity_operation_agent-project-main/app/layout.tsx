import type React from "react"
import type { Metadata, Viewport } from "next"
import { Fredoka, Nunito, VT323 } from "next/font/google"
import { generateSEOMetadata } from "@/lib/seo/generateMetadata"
import { METADATA } from "@/lib/constants"
import "./globals.css"

const fredoka = Fredoka({
  subsets: ["latin"],
  variable: "--font-fredoka",
  weight: ["400", "500", "600", "700"],
})
const nunito = Nunito({
  subsets: ["latin"],
  variable: "--font-nunito",
  weight: ["400", "500", "600", "700", "800"],
})
const vt323 = VT323({
  subsets: ["latin"],
  variable: "--font-vt323",
  weight: ["400"],
})

export const metadata: Metadata = {
  ...generateSEOMetadata({
    title: METADATA.TITLE,
    description: METADATA.DESCRIPTION,
    keywords: [...METADATA.KEYWORDS],
  }),
  generator: 'v0.dev',
  icons: {
    icon: [
      { url: '/icon.png', type: 'image/png' },
    ],
    shortcut: '/icon.png',
    apple: '/icon.png',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${fredoka.variable} ${nunito.variable} ${vt323.variable}`}>
      <body className={`${nunito.className} antialiased`}>{children}</body>
    </html>
  )
}

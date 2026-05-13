import { Inter } from "next/font/google"
import "./globals.css"
import type { Metadata } from "next"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: "Ghost Job Detector - Analyze Job Postings for Legitimacy",
  description: "Verify if job postings are real or ghost jobs. Analyze job descriptions, check ATS verification, and see community reports to make informed decisions.",
  keywords: ["ghost jobs", "job posting analyzer", "fake job detector", "job search", "linkedin jobs"],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} bg-background`}>
      <body className="min-h-screen font-sans antialiased">
        {children}
      </body>
    </html>
  )
}

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Chef Candidate Evaluation Platform',
  description: 'Evaluate chef candidates for menu-development and test-kitchen roles',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

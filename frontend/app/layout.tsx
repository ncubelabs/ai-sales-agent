import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Sales Agent | NCube Labs',
  description: 'Personalized video outreach in seconds',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Background effects */}
        <div className="fixed inset-0 bg-gradient-glow pointer-events-none" />
        <div className="fixed inset-0 bg-grid-pattern pointer-events-none opacity-50" />
        
        {/* Main content */}
        <main className="relative z-10 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}

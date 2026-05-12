import type { Metadata } from 'next'
import { Cinzel_Decorative, Cinzel, Rajdhani } from 'next/font/google'
import { Providers } from '@/components/Providers'
import '../styles/globals.css'

const cinzelDecorative = Cinzel_Decorative({
  weight: ['400', '700', '900'],
  subsets: ['latin'],
  variable: '--font-cinzel-decorative',
})
const cinzel = Cinzel({
  weight: ['400', '600', '700'],
  subsets: ['latin'],
  variable: '--font-cinzel',
})
const rajdhani = Rajdhani({
  weight: ['300', '400', '500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-rajdhani',
})

export const metadata: Metadata = {
  title: 'BitmojiGuy 5-Min Credit Fix — AE Labs',
  description: '5 Min. 5 Clicks. It\'s Fixed. AI-powered credit dispute letters.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${cinzelDecorative.variable} ${cinzel.variable} ${rajdhani.variable}`}>
      <body>
        <Providers>{children}</Providers>
        <footer style={{ padding: '12px 24px', textAlign: 'center', fontSize: 10, color: '#5A5A5A', fontFamily: 'var(--font-rajdhani), sans-serif', lineHeight: 1.5, borderTop: '1px solid rgba(90,90,90,0.15)' }}>
          This tool is for advisory and fintech purposes only. It is not credit counseling, credit repair, or legal counsel. Results are not guaranteed. Use of this tool does not establish an attorney-client relationship. Consult a licensed professional for legal or financial advice. &copy; {new Date().getFullYear()} Arden Edge Capital.
        </footer>
      </body>
    </html>
  )
}

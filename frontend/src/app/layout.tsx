import type { Metadata } from 'next';
import { Bangers, DM_Sans } from 'next/font/google';
import './globals.css';

const dmSans = DM_Sans({
  variable: '--font-dm-sans',
  subsets: ['latin'],
  weight: ['400', '500', '700'],
});

const bangers = Bangers({
  variable: '--font-bangers',
  subsets: ['latin'],
  weight: '400',
});

export const metadata: Metadata = {
  title: '5-Min Credit Fix — AE Labs',
  description: 'Upload your credit report. Auto-detect disputes. Generate legal letters for all 3 bureaus.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${dmSans.variable} ${bangers.variable} h-full`}>
      <body className="min-h-full bg-[#050508] text-[#E0DDE6] font-sans antialiased overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}

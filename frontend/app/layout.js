import "./globals.css";

export const metadata = {
  title: "Five-Minute Credit Fix — Become the Warrior Your Credit Deserves",
  description: "Professional FCRA dispute letters in 5 minutes. Your credit is a battle. We are your armor.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen relative overflow-x-hidden">
        {/* Kanji Watermarks — rotating background seals */}
        <div className="kanji-watermark kanji-1" aria-hidden="true">武</div>
        <div className="kanji-watermark kanji-2" aria-hidden="true">信</div>
        <div className="kanji-watermark kanji-3" aria-hidden="true">力</div>

        {/* Atmospheric Petals */}
        <div className="petal" style={{ left: '10%', animationDuration: '8s', animationDelay: '0s' }} aria-hidden="true" />
        <div className="petal" style={{ left: '25%', animationDuration: '6s', animationDelay: '2s' }} aria-hidden="true" />
        <div className="petal" style={{ left: '55%', animationDuration: '7s', animationDelay: '4s' }} aria-hidden="true" />
        <div className="petal" style={{ left: '80%', animationDuration: '9s', animationDelay: '1s' }} aria-hidden="true" />
        <div className="petal" style={{ left: '40%', animationDuration: '5s', animationDelay: '3s' }} aria-hidden="true" />

        {/* Header */}
        <header className="border-b border-gold-border bg-lacquer/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <a href="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-lg bg-gold flex items-center justify-center font-bold text-lacquer text-sm group-hover:shadow-[0_0_12px_rgba(212,175,55,0.4)] transition-shadow duration-200">
                AE
              </div>
              <span className="font-heading font-semibold text-lg tracking-tight text-gold">
                5-Min Credit Fix
              </span>
            </a>
            <nav className="flex items-center gap-6 font-heading text-sm">
              <a
                href="/dojo"
                className="text-gold/70 hover:text-gold transition-colors duration-200"
              >
                The Dojo
              </a>
              <span className="text-muted/40 text-xs font-body">Arden Edge Labs</span>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="relative z-10 max-w-5xl w-full mx-auto px-6 py-10">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-gold-border py-6 text-center text-xs text-muted/50 font-body relative z-10">
          &copy; {new Date().getFullYear()} Arden Edge Labs &middot; Your credit is a battle. We are your armor.
        </footer>
      </body>
    </html>
  );
}

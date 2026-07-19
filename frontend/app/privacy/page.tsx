import Link from 'next/link'

export const metadata = { title: 'Privacy Policy — 5-Min Credit Fix' }

const SECTIONS = [
  {
    title: '1. What We Collect',
    body: `To prepare your dispute letters we collect: your name, mailing address, date of birth, last 4 digits of your SSN, phone, email, the documents you upload (government ID, proof of address, credit report), and the dispute items you confirm. We also receive payment confirmation (not card numbers) from Stripe and mail tracking data from our mailing provider.`,
  },
  {
    title: '2. The 24-Hour Rule',
    body: `Every case record — including all personal information, uploaded documents, and generated letters — is permanently and irreversibly deleted from our systems within 24 hours of the session being created. There are no backups of your personal data after deletion. Download your letter packet before then.`,
  },
  {
    title: '3. Encryption',
    body: `Personal information is encrypted at rest using AES-256-GCM before it reaches our database, and uploaded documents are encrypted with a per-session key before they touch disk. Data in transit is protected by TLS. Our database provider sees only ciphertext.`,
  },
  {
    title: '4. What We Never Do',
    body: `We do not sell, rent, or share your personal information. We do not use your credit data for marketing. We do not retain your data to "make the next time easier" — each dispute round starts fresh, by design.`,
  },
  {
    title: '5. Service Providers',
    body: `We use Stripe (payments), a print-and-mail provider (letter mailing), and an email provider (sending your PDF packet). Each receives only what it needs to perform its function. If AI-assisted report scanning is enabled, report text is processed transiently to detect disputable items and is not used for model training by us.`,
  },
  {
    title: '6. Your Rights',
    body: `Because data is deleted within 24 hours automatically, deletion requests are usually moot — but you may contact us at any time about your data. California residents: we do not sell personal information as defined by the CCPA/CPRA.`,
  },
  {
    title: '7. Contact',
    body: `Privacy questions: noreply@ardanedgecapital.com.`,
  },
]

const GOLD = '#C9A84C'

export default function PrivacyPage() {
  return (
    <div style={{ position: 'relative', zIndex: 5, maxWidth: 800, margin: '0 auto', padding: '2.5rem 1.25rem 5rem' }}>
      <Link href="/" style={{
        fontFamily: 'var(--font-cinzel), serif', fontSize: 12, letterSpacing: 2,
        textTransform: 'uppercase', color: '#8A8278', textDecoration: 'none',
      }}>
        &larr; Back to the Journey
      </Link>
      <h1 style={{
        fontFamily: 'var(--font-cinzel-decorative), serif', fontSize: '2rem',
        color: GOLD, letterSpacing: 2, margin: '18px 0 4px',
        textShadow: `0 0 24px ${GOLD}44`,
      }}>
        Privacy Policy
      </h1>
      <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: '#8A8278', marginBottom: 28 }}>
        Last updated: July 18, 2026
      </p>
      {SECTIONS.map((s) => (
        <div key={s.title} style={{
          background: 'rgba(0,0,0,0.4)', border: `1px solid ${GOLD}22`,
          borderRadius: 6, padding: '18px 20px', marginBottom: 12,
        }}>
          <h2 style={{
            fontFamily: 'var(--font-heading)', fontSize: 15, color: '#F0EBE0',
            letterSpacing: 0.5, marginBottom: 8,
          }}>
            {s.title}
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#A8A29A', lineHeight: 1.7, margin: 0 }}>
            {s.body}
          </p>
        </div>
      ))}
    </div>
  )
}

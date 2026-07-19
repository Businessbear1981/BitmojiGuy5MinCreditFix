import { Header } from '@/components/Header';
import { Card } from '@/components/ui/Card';

export const metadata = { title: 'Privacy Policy — 5-Min Credit Fix' };

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
];

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <div className="relative z-[5] max-w-[800px] mx-auto px-5 py-10 pb-20">
        <h1 className="font-bangers text-[36px] tracking-wider text-teal-400 drop-shadow-[0_0_12px_rgba(0,212,212,0.3)] mb-2">
          Privacy Policy
        </h1>
        <p className="text-[12px] text-gray-500 mb-8">Last updated: July 18, 2026</p>
        {SECTIONS.map((s) => (
          <Card key={s.title}>
            <h2 className="text-[15px] font-bold text-gray-200 mb-2">{s.title}</h2>
            <p className="text-[13px] text-gray-400 leading-relaxed">{s.body}</p>
          </Card>
        ))}
      </div>
    </>
  );
}

import { Header } from '@/components/Header';
import { Card } from '@/components/ui/Card';

export const metadata = { title: 'Terms of Service — 5-Min Credit Fix' };

const SECTIONS = [
  {
    title: '1. What This Service Is',
    body: `AE 5-Min Credit Fix ("the Service") is self-help document preparation software operated by AE Labs / Arden Edge Capital ("AE Labs"). The Service helps you prepare dispute letters, from information and documents you provide, that you send (or authorize us to mail on your behalf) to consumer reporting agencies and creditors under rights you already have for free under the Fair Credit Reporting Act (FCRA) and Fair Debt Collection Practices Act (FDCPA).`,
  },
  {
    title: '2. What This Service Is Not',
    body: `AE Labs is not a law firm, does not provide legal advice, and no attorney-client relationship is created by using the Service. The Service does not review, negotiate, or settle debts, does not contact bureaus or creditors to advocate on your behalf, and does not promise or guarantee any change to your credit report or credit score. You can dispute items on your credit report yourself at no cost by contacting the bureaus directly.`,
  },
  {
    title: '3. Your Responsibilities',
    body: `You confirm that all information and documents you provide are accurate and belong to you, and that every item you choose to dispute is disputed in good faith. Submitting knowingly false disputes may violate federal law. You are responsible for reviewing each generated letter before it is mailed.`,
  },
  {
    title: '4. Payment',
    body: `The one-time fee of $24.99 is charged for the preparation of your dispute letter packet and, where configured, round-1 mailing. Follow-up dispute rounds are initiated by you by re-running the flow. Payments are processed by Stripe; AE Labs does not store your card details.`,
  },
  {
    title: '5. Data Handling',
    body: `Your information is encrypted at rest and permanently deleted from our systems within 24 hours of your session's creation. Download your letter packet promptly. See the Privacy Policy for full details.`,
  },
  {
    title: '6. Beta Availability',
    body: `During the beta period the Service is available only to residents of Texas, California, and Washington, and regional capacity limits may apply.`,
  },
  {
    title: '7. Disclaimers & Limitation of Liability',
    body: `The Service is provided "as is" without warranties of any kind. Dispute outcomes depend on the bureaus, furnishers, and the accuracy of your report — results vary and no outcome is guaranteed. To the maximum extent permitted by law, AE Labs' total liability arising from the Service is limited to the amount you paid for it.`,
  },
  {
    title: '8. Contact',
    body: `Questions about these terms: noreply@ardanedgecapital.com.`,
  },
];

export default function TermsPage() {
  return (
    <>
      <Header />
      <div className="relative z-[5] max-w-[800px] mx-auto px-5 py-10 pb-20">
        <h1 className="font-bangers text-[36px] tracking-wider text-teal-400 drop-shadow-[0_0_12px_rgba(0,212,212,0.3)] mb-2">
          Terms of Service
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

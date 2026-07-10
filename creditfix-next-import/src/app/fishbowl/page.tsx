import { Header } from '@/components/Header';
import { Card, CardTitle } from '@/components/ui/Card';

const FACTORS = [
  { label: 'Payment History', pct: 35, color: 'bg-purple-500', shadow: 'shadow-[0_0_8px_rgba(168,85,200,0.3)]', textColor: 'text-purple-400' },
  { label: 'Amounts Owed', pct: 30, color: 'bg-teal-400', shadow: 'shadow-[0_0_8px_rgba(0,212,212,0.3)]', textColor: 'text-teal-400' },
  { label: 'Length of History', pct: 15, color: 'bg-yellow-400', shadow: 'shadow-[0_0_8px_rgba(212,184,96,0.3)]', textColor: 'text-yellow-400' },
  { label: 'New Credit', pct: 10, color: 'bg-green-400', shadow: 'shadow-[0_0_8px_rgba(0,255,136,0.3)]', textColor: 'text-green-400' },
  { label: 'Credit Mix', pct: 10, color: 'bg-violet-400', shadow: 'shadow-[0_0_8px_rgba(155,89,182,0.3)]', textColor: 'text-violet-400' },
];

const GLOSSARY = [
  { term: 'CRA', def: 'Credit Reporting Agency — Equifax, Experian, TransUnion.' },
  { term: 'FCRA', def: 'Fair Credit Reporting Act — Federal law governing credit reporting accuracy.' },
  { term: 'FDCPA', def: 'Fair Debt Collection Practices Act — Regulates debt collector behavior.' },
  { term: 'MOV', def: 'Method of Verification — How a bureau verified disputed information.' },
  { term: 'CFPB', def: 'Consumer Financial Protection Bureau — Federal agency overseeing credit bureaus.' },
  { term: 'SOL', def: 'Statute of Limitations — Time period for a creditor to sue for a debt.' },
  { term: 'DOFD', def: 'Date of First Delinquency — Starts the 7-year reporting clock.' },
  { term: 'e-OSCAR', def: 'Automated system bureaus use to communicate with furnishers during disputes.' },
];

export default function FishbowlPage() {
  return (
    <>
      <Header />
      <div className="relative z-[5] max-w-[800px] mx-auto px-5 py-10 pb-20">
        {/* Disclaimer */}
        <div className="bg-purple-500/[0.06] border border-purple-500/20 rounded-xl px-6 py-5 mb-8 text-[13px] leading-relaxed">
          <strong className="text-purple-400 uppercase tracking-wider block mb-1.5">Educational Information Only</strong>
          This page is for educational purposes only and does not constitute legal, financial, or credit repair advice. AE Labs / Arden Edge Capital is not a law firm. Consult a licensed attorney for legal advice.
        </div>

        {/* Timeline */}
        <section className="mb-10">
          <h2 className="font-bangers text-[32px] tracking-wider text-teal-400 drop-shadow-[0_0_12px_rgba(0,212,212,0.3)] mb-4">Dispute Timeline</h2>
          <Card>
            <div className="relative pl-8 space-y-6">
              <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-teal-400 via-purple-500 to-yellow-400" />
              {[
                { day: '0', title: 'Mail Dispute Letters', desc: 'Send via certified mail with return receipt.', color: 'border-teal-400 text-teal-400 bg-teal-400/10 shadow-[0_0_8px_rgba(0,212,212,0.2)]' },
                { day: '30', title: 'Bureau Response Deadline', desc: 'Under FCRA 611(a)(1), bureaus must respond within 30 days.', color: 'border-purple-500 text-purple-400 bg-purple-500/10 shadow-[0_0_8px_rgba(168,85,200,0.2)]' },
                { day: '45', title: 'Request Method of Verification', desc: 'Demand MOV under FCRA 611(a)(6)(B)(iii).', color: 'border-yellow-400 text-yellow-400 bg-yellow-400/10 shadow-[0_0_8px_rgba(212,184,96,0.2)]' },
                { day: '60', title: 'Escalation Letter', desc: 'Send 60-day follow-up citing inadequate response.', color: 'border-yellow-400 text-yellow-400 bg-yellow-400/10 shadow-[0_0_8px_rgba(212,184,96,0.2)]' },
                { day: '90', title: 'Regulatory Complaints', desc: 'File with CFPB, FTC, and state Attorney General.', color: 'border-green-400 text-green-400 bg-green-400/10 shadow-[0_0_8px_rgba(0,255,136,0.2)]' },
              ].map((item) => (
                <div key={item.day} className="relative">
                  <div className={`absolute -left-8 top-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center text-[11px] font-bold ${item.color}`}>{item.day}</div>
                  <div className="text-[15px] font-bold mb-1">{item.title}</div>
                  <div className="text-[13px] text-gray-500 leading-relaxed">{item.desc}</div>
                </div>
              ))}
            </div>
          </Card>
        </section>

        {/* FICO factors */}
        <section className="mb-10">
          <h2 className="font-bangers text-[32px] tracking-wider text-teal-400 drop-shadow-[0_0_12px_rgba(0,212,212,0.3)] mb-4">How Credit Scoring Works</h2>
          <Card>
            {FACTORS.map((f) => (
              <div key={f.label} className="flex items-center gap-3 mb-3">
                <span className="text-[13px] font-bold min-w-[140px] text-gray-300">{f.label}</span>
                <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${f.color} ${f.shadow}`} style={{ width: `${f.pct}%` }} />
                </div>
                <span className={`text-xs font-bold min-w-[36px] text-right ${f.textColor}`}>{f.pct}%</span>
              </div>
            ))}
          </Card>
        </section>

        {/* Glossary */}
        <section className="mb-10">
          <h2 className="font-bangers text-[32px] tracking-wider text-teal-400 drop-shadow-[0_0_12px_rgba(0,212,212,0.3)] mb-4">Glossary</h2>
          <Card>
            {GLOSSARY.map((g) => (
              <div key={g.term} className="flex gap-3 py-3 border-b border-white/[0.03] last:border-b-0">
                <span className="font-bold text-yellow-400 min-w-[80px] text-[13px] shrink-0">{g.term}</span>
                <span className="text-[13px] text-gray-400 leading-relaxed">{g.def}</span>
              </div>
            ))}
          </Card>
        </section>

        {/* Disclaimer bottom */}
        <div className="bg-purple-500/[0.06] border border-purple-500/20 rounded-xl px-6 py-5 text-[13px] leading-relaxed">
          <strong className="text-purple-400 uppercase tracking-wider block mb-1.5">Reminder</strong>
          Nothing on this page is legal advice. Credit dispute outcomes vary. AE Labs provides tools and templates — not legal representation.
        </div>
      </div>
    </>
  );
}

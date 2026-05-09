"use client";

import { useState } from "react";

export default function TermsGate({ api, onAccept }) {
  const [checked, setChecked] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function accept() {
    setSubmitting(true);
    try {
      const res = await fetch(`${api}/api/terms/accept`, { method: "POST" });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      onAccept(data.terms_token);
    } catch {
      onAccept("dev-mode");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-lacquer/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-gold-border rounded-xl max-w-lg w-full p-6 max-h-[85vh] flex flex-col">
        <h2 className="text-xl font-bold mb-4 font-heading text-gold">Terms of Service</h2>

        <div className="flex-1 overflow-y-auto text-sm text-muted space-y-3 mb-6 pr-2 font-body">
          <p>
            <strong className="text-ivory">AE 5-Min Credit Fix</strong> is a
            self-help document preparation tool provided by Arden Edge Labs. By
            using this service you agree to the following:
          </p>

          <p>
            <strong className="text-gold/80">1. Not Legal Advice.</strong> This
            tool generates dispute letter templates based on your input. It does
            not provide legal advice. We are not a law firm or credit repair
            organization. You are responsible for reviewing all letters before
            mailing them.
          </p>

          <p>
            <strong className="text-gold/80">2. Accuracy of Information.</strong>{" "}
            You certify that all information you provide is accurate and
            pertains to your own credit file. You will not use this tool to
            submit false or fraudulent disputes.
          </p>

          <p>
            <strong className="text-gold/80">3. Data Handling.</strong> All
            uploaded documents are encrypted with a unique per-session key
            (AES-256-GCM). Unencrypted data is never written to disk. All
            session data is automatically deleted after 24 hours. We log session
            IDs only &mdash; never file contents or personal information.
          </p>

          <p>
            <strong className="text-gold/80">4. One-Time Fee.</strong> The
            $24.99 fee is a one-time charge for document preparation. It is
            non-refundable once letters have been generated and delivered.
            Certified mail postage costs are separate and charged by USPS.
          </p>

          <p>
            <strong className="text-gold/80">5. FCRA Compliance.</strong>{" "}
            Letters reference the Fair Credit Reporting Act (15 U.S.C. &sect;1681 et
            seq.), specifically Sections 609, 611, and 623. Results are not
            guaranteed. Bureau response times and outcomes vary.
          </p>

          <p>
            <strong className="text-gold/80">6. Limitation of Liability.</strong>{" "}
            Arden Edge Labs and its affiliates shall not be liable for any
            damages arising from your use of this tool or the outcome of any
            dispute filed using generated letters.
          </p>

          <p className="text-xs text-muted/60">
            Last updated: May 2026. Texas law governs these terms.
          </p>
        </div>

        <label className="flex items-start gap-3 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={checked}
            onChange={() => setChecked(!checked)}
            className="mt-1 w-4 h-4 rounded border-gold/40 bg-lacquer text-gold focus:ring-gold focus:ring-offset-0"
          />
          <span className="text-sm text-ivory/80 font-body">
            I have read and agree to the Terms of Service. I understand this is
            not legal advice and that my data will be encrypted and
            auto-deleted after 24 hours.
          </span>
        </label>

        <button
          onClick={accept}
          disabled={!checked || submitting}
          className="btn-gold w-full py-3"
        >
          {submitting ? "..." : "I Agree — Begin My Quest"}
        </button>
      </div>
    </div>
  );
}

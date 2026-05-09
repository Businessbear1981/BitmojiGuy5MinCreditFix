"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import PartnerCards from "../../components/PartnerCards";
import MrBeeks from "../../components/MrBeeks";

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function DojoPage() {
  const router = useRouter();
  const [resumeId, setResumeId] = useState("");
  const [resumeError, setResumeError] = useState("");

  async function resumeSession() {
    if (!resumeId.trim()) return;
    setResumeError("");
    try {
      const res = await fetch(`${API}/api/case/${resumeId.trim()}/status`);
      if (!res.ok) throw new Error("Session not found");
      router.push(`/?session_id=${resumeId.trim()}`);
    } catch {
      setResumeError("Session not found. Check your session ID.");
    }
  }

  return (
    <div>
      {/* Hero */}
      <div className="text-center mb-12">
        <MrBeeks stage={1} size="medium" />
        <h1 className="mt-6 mb-2">The Dojo</h1>
        <p className="text-muted font-body text-lg">
          Your credit repair command center. Every warrior starts here.
        </p>
      </div>

      {/* Get Your Report */}
      <div className="card mb-6">
        <h2 className="step-sub text-xl font-semibold mb-2">
          Upload Your Battle Plans
        </h2>
        <p className="text-muted text-sm mb-4 font-body">
          You have the right to one free credit report per year from each bureau.
          Get them all at AnnualCreditReport.com. No credit card required. No tricks.
        </p>
        <a
          href="https://www.annualcreditreport.com"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-gold"
        >
          Get Your Free Credit Report &rarr;
        </a>
        <p className="text-muted/60 text-xs mt-3 font-body">
          AnnualCreditReport.com &mdash; the only federally authorized source for
          free reports from Experian, Equifax, and TransUnion.
        </p>
      </div>

      {/* Start Dispute */}
      <div className="card mb-6">
        <h2 className="step-sub text-xl font-semibold mb-2">
          Begin Your Quest
        </h2>
        <p className="text-muted text-sm mb-4 font-body">
          Your credit is a battle. The bureaus are the enemy. Errors on your
          report are their weapons. Silence is your defeat. In five minutes,
          you&apos;ll have professional dispute letters ready to send.
        </p>
        <a href="/" className="btn-outline">
          Launch 5-Min Credit Fix &rarr;
        </a>
      </div>

      {/* Resume */}
      <div className="card mb-6">
        <h2 className="step-sub text-xl font-semibold mb-2">
          Resume a Session
        </h2>
        <p className="text-muted text-sm mb-4 font-body">
          Already started? Enter your session ID to pick up where you left off.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Enter your session ID"
            value={resumeId}
            onChange={(e) => setResumeId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && resumeSession()}
            className="input-field font-mono text-sm"
          />
          <button onClick={resumeSession} className="btn-outline whitespace-nowrap">
            Resume
          </button>
        </div>
        {resumeError && (
          <p className="mt-2 text-crimson text-sm">{resumeError}</p>
        )}
      </div>

      {/* Partner Cards */}
      <div className="card mb-6">
        <PartnerCards />
      </div>

      {/* How It Works — The Path of Five */}
      <div className="card">
        <h2 className="step-sub text-xl font-semibold mb-4">
          The Path of Five
        </h2>
        <div className="space-y-3">
          {[
            { icon: "道", title: "The Dojo", desc: "Enter your details and upload your credit report" },
            { icon: "鯉", title: "The Koi Pond", desc: "Our AI scans your report and flags every disputable item" },
            { icon: "庭", title: "The Sand Garden", desc: "FCRA-compliant dispute letters generated for each item" },
            { icon: "階", title: "The Stairway", desc: "$24.99 — send letters via USPS Certified Mail with tracking" },
            { icon: "門", title: "The Dragon Gate", desc: "Victory awaits. Track bureau response deadlines." },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-gold/10 border border-gold-border flex items-center justify-center text-gold text-lg flex-shrink-0 font-heading">
                {item.icon}
              </div>
              <div>
                <div className="font-heading text-gold text-sm font-semibold">{item.title}</div>
                <div className="text-muted text-xs font-body">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

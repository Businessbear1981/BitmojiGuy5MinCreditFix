"use client";

import { useState } from "react";

export default function StepUpload({ api, sessionId, setSessionId, suggestions, setSuggestions, termsToken, onNext }) {
  const [form, setForm] = useState({
    name: "",
    address: "",
    dob: "",
    ssn_last4: "",
    phone: "",
    email: "",
  });
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState(!!sessionId);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function createCase() {
    setError("");
    try {
      const res = await fetch(`${api}/api/case`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Terms-Token": termsToken || "",
        },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to create case");
      }
      const data = await res.json();
      setSessionId(data.session_id);
      setCreated(true);
    } catch (err) {
      setError(err.message);
    }
  }

  async function uploadFiles() {
    if (files.length === 0) {
      onNext();
      return;
    }
    setUploading(true);
    setError("");
    try {
      let allSuggestions = [];
      for (const file of files) {
        const fd = new FormData();
        fd.append("file", file);
        const res = await fetch(`${api}/api/case/${sessionId}/upload`, {
          method: "POST",
          body: fd,
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || `Failed to upload ${file.name}`);
        }
        const data = await res.json();
        setUploadedFiles((prev) => [...prev, file.name]);
        if (data.suggestions && data.suggestions.length > 0) {
          allSuggestions = [...allSuggestions, ...data.suggestions];
        }
      }
      if (allSuggestions.length > 0) {
        setSuggestions(allSuggestions);
      }
      onNext();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  const fields = [
    { key: "name", label: "Your Name", type: "text", placeholder: "As you wish to appear on letters" },
    { key: "address", label: "Mailing Address", type: "text", placeholder: "Your current address for bureau correspondence" },
    { key: "dob", label: "Date of Birth", type: "date" },
    { key: "ssn_last4", label: "SSN (last 4)", type: "text", placeholder: "For identity verification only", maxLength: 4 },
    { key: "phone", label: "Phone Number", type: "tel", placeholder: "For urgent updates" },
    { key: "email", label: "Email Address", type: "email", placeholder: "Where we'll send your progress" },
  ];

  return (
    <div>
      <h2 className="step-header text-2xl font-bold mb-2">The Dojo</h2>
      <p className="text-muted mb-4 font-body">
        Every warrior starts here. Tell us about your credit battle.
        We&apos;ll listen, learn, and prepare you for what comes next.
      </p>

      <div className="mb-6 msg-info">
        <span className="text-gold font-semibold">Don&apos;t have your credit report?</span>{" "}
        <a
          href="https://www.annualcreditreport.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gold underline hover:text-gold-light font-medium"
        >
          Get all 3 free at AnnualCreditReport.com
        </a>
        <span className="text-muted ml-1">&mdash; no credit card required, no tricks.</span>
      </div>

      {!created ? (
        <div className="space-y-4">
          {fields.map((f) => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gold/80 mb-1 font-heading">
                {f.label}
              </label>
              <input
                type={f.type}
                placeholder={f.placeholder || ""}
                maxLength={f.maxLength}
                value={form[f.key]}
                onChange={(e) => update(f.key, e.target.value)}
                className="input-field"
              />
            </div>
          ))}
          <button
            onClick={createCase}
            disabled={!form.name || !form.address || !form.dob || !form.ssn_last4 || !form.email}
            className="btn-gold w-full py-3 text-base"
          >
            Begin Training
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="msg-success">
            Your armor grows stronger. Session:{" "}
            <code className="font-mono bg-jade/10 px-1 rounded">
              {sessionId}
            </code>
            <span className="block mt-1 text-jade/60 text-xs">
              Save this ID to resume your session later.
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gold/80 mb-2 font-heading">
              Upload Your Battle Plans
            </label>
            <p className="text-sm text-muted mb-3 font-body">
              Your credit report is the map to victory. Upload it here.
              We&apos;ll read every line, identify every error, and prepare your counter-strike.
            </p>
            <div className="border-2 border-dashed border-gold-border rounded-lg p-6 text-center hover:border-gold/40 transition-colors">
              <input
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.txt,.csv"
                onChange={(e) => setFiles(Array.from(e.target.files))}
                className="w-full text-sm text-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-gold/10 file:text-gold hover:file:bg-gold/20 font-body"
              />
              <p className="text-xs text-muted/60 mt-2 font-body">
                Drag and drop your credit report here, or click to browse.
                PDF, CSV, TXT &mdash; max 10MB each
              </p>
            </div>
            {files.length > 0 && (
              <p className="text-xs text-muted mt-2 font-body">
                {files.length} file(s) selected: {files.map((f) => f.name).join(", ")}
              </p>
            )}
            {uploadedFiles.length > 0 && (
              <div className="mt-2 text-xs text-jade">
                Uploaded: {uploadedFiles.join(", ")}
              </div>
            )}
          </div>

          <button
            onClick={uploadFiles}
            disabled={uploading}
            className="btn-gold w-full py-3 text-base"
          >
            {uploading
              ? "Analyzing your battle plans..."
              : files.length > 0
              ? "Upload & Advance"
              : "Skip Upload & Advance"}
          </button>
        </div>
      )}

      {error && <p className="mt-4 msg-error">{error}</p>}
    </div>
  );
}

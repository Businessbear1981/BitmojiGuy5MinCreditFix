import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [session, setSession] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");

  async function createSession() {
    try {
      const res = await fetch(`${API_URL}/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          address,
        }),
      });

      if (!res.ok) throw new Error("Failed to create session");

      const data = await res.json();
      setSession(data.session_id);
      setPreview(data.preview);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={{ padding: 40, fontFamily: "Arial", maxWidth: 600 }}>
      <h1>Bitmoji Credit Tool</h1>

      <label>Name</label>
      <input
        style={{ width: "100%", marginBottom: 10 }}
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <label>Address</label>
      <input
        style={{ width: "100%", marginBottom: 10 }}
        value={address}
        onChange={(e) => setAddress(e.target.value)}
      />

      <button
        style={{ padding: 10, marginTop: 10 }}
        onClick={createSession}
      >
        Generate Letters
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {session && (
        <div style={{ marginTop: 20 }}>
          <h3>Preview:</h3>
          <pre style={{ padding: 10, background: "#eee" }}>{preview}</pre>
        </div>
      )}
    </div>
  );
}

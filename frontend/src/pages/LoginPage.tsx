import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Lock } from "lucide-react";
import { api } from "../lib/api";
import { useAuthStore } from "../stores/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("admin@arl.local");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      const me = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setAuth(data.access_token, me.data);
      navigate("/");
    } catch {
      setError("Invalid credentials or API unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-mesh px-4">
      <div className="arl-grid-bg absolute inset-0 opacity-60" />
      <div className="pointer-events-none absolute -left-20 top-10 h-72 w-72 rounded-full bg-signal/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-10 bottom-10 h-80 w-80 rounded-full bg-signal-info/20 blur-3xl" />

      <div className="relative z-10 w-full max-w-md animate-fade-up">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-signal/20 text-signal">
            <Activity className="h-7 w-7" />
          </div>
          <h1 className="font-display text-4xl font-semibold tracking-tight text-paper">
            Adverse Risk Lookup
          </h1>
          <p className="mt-3 text-sm text-paper/65">
            Transforming Global Banking News into Actionable Risk Intelligence
          </p>
        </div>

        <form onSubmit={onSubmit} className="arl-panel space-y-4 p-6">
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-paper/50">Email</label>
            <input
              className="arl-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-paper/50">Password</label>
            <input
              className="arl-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-signal-danger">{error}</p>}
          <button className="arl-btn w-full" type="submit" disabled={loading}>
            <Lock className="h-4 w-4" />
            {loading ? "Signing in…" : "Sign in to ARL"}
          </button>
          <p className="text-center text-[11px] text-paper/45">
            Demo: admin@arl.local / ChangeMe123!
          </p>
        </form>
      </div>
    </div>
  );
}

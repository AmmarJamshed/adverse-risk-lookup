import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, ShieldCheck } from "lucide-react";
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
    <div className="flex min-h-screen bg-steel-50">
      <section className="relative hidden w-[46%] flex-col justify-between bg-navy-900 px-10 py-12 text-white lg:flex">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-brand text-sm font-bold">
              ARL
            </div>
            <div>
              <div className="text-lg font-semibold">Adverse Risk Lookup</div>
              <div className="text-[11px] uppercase tracking-[0.16em] text-white/50">
                Obligations workstation
              </div>
            </div>
          </div>
          <h1 className="mt-16 max-w-md text-4xl font-semibold leading-tight tracking-tight">
            Horizon scan. Assess applicability. Close the control gap.
          </h1>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-white/70">
            Turn UK, USA, EU, and Pakistan regulatory change into an obligations register and
            gap-analysis cases mapped to your policies and controls.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs">
          {[
            ["Scan", "Regulatory horizon"],
            ["Assess", "Applicability"],
            ["Map", "Policies & controls"],
          ].map(([k, v]) => (
            <div key={k} className="rounded-sm border border-white/10 bg-white/5 p-3">
              <div className="font-semibold text-brand-mid">{k}</div>
              <div className="mt-1 text-white/60">{v}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-[420px]">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2 text-navy-900">
              <div className="flex h-9 w-9 items-center justify-center rounded-sm bg-navy-900 text-xs font-bold text-white">
                ARL
              </div>
              <div className="font-semibold">Adverse Risk Lookup</div>
            </div>
          </div>

          <div className="arl-panel p-7">
            <div className="mb-6 flex items-start gap-3">
              <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-sm bg-brand-soft text-brand">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-navy-900 dark:text-white">Sign in</h2>
                <p className="mt-1 text-sm text-steel-500">Access your regulatory obligations workspace</p>
              </div>
            </div>

            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-steel-500">
                  Email
                </label>
                <input
                  className="arl-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="username"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-steel-500">
                  Password
                </label>
                <input
                  className="arl-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>
              {error && <p className="text-sm font-medium text-hit-critical">{error}</p>}
              <button className="arl-btn-primary w-full" type="submit" disabled={loading}>
                <Lock className="h-4 w-4" />
                {loading ? "Authenticating…" : "Continue to console"}
              </button>
            </form>

            <div className="mt-5 border-t border-steel-200 pt-4 text-xs text-steel-500 dark:border-navy-700">
              Demo access: <span className="font-mono text-steel-700 dark:text-steel-300">admin@arl.local</span> /{" "}
              <span className="font-mono text-steel-700 dark:text-steel-300">ChangeMe123!</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

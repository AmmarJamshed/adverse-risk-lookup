import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function AlertsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("High severity cyber");
  const [severityMin, setSeverityMin] = useState("high");
  const [country, setCountry] = useState("");

  const { data: subs = [] } = useQuery({
    queryKey: ["alert-subs"],
    queryFn: async () => (await api.get("/alerts/subscriptions")).data,
  });
  const { data: notes = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get("/notifications")).data,
  });

  async function createSub(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/alerts/subscriptions", {
      name,
      conditions: {
        severity_min: severityMin,
        ...(country ? { country } : {}),
      },
      channels: ["dashboard"],
    });
    qc.invalidateQueries({ queryKey: ["alert-subs"] });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Alerts & Notifications</h1>
        <p className="text-sm text-paper/60">Subscribe to severity, country, and category conditions</p>
      </div>

      <form onSubmit={createSub} className="arl-panel grid gap-3 p-4 md:grid-cols-4">
        <input className="arl-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Alert name" />
        <select className="arl-input" value={severityMin} onChange={(e) => setSeverityMin(e.target.value)}>
          <option value="medium">Severity ≥ medium</option>
          <option value="high">Severity ≥ high</option>
          <option value="critical">Severity ≥ critical</option>
        </select>
        <input className="arl-input" value={country} onChange={(e) => setCountry(e.target.value)} placeholder="Country (optional)" />
        <button className="arl-btn" type="submit">
          Subscribe
        </button>
      </form>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="arl-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase">Subscriptions</h2>
          {subs.map((s: { id: string; name: string; conditions: Record<string, unknown> }) => (
            <div key={s.id} className="mb-2 rounded border border-white/10 p-3 text-sm">
              <div className="font-medium">{s.name}</div>
              <pre className="mt-1 overflow-auto text-[11px] text-paper/50">{JSON.stringify(s.conditions)}</pre>
            </div>
          ))}
        </div>
        <div className="arl-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase">Inbox</h2>
          {notes.map((n: { id: string; title: string; body: string; severity: string }) => (
            <div key={n.id} className="mb-2 rounded border border-white/10 p-3 text-sm">
              <div className="font-medium">{n.title}</div>
              <div className="text-xs text-signal">{n.severity}</div>
              <p className="mt-1 text-paper/70">{n.body}</p>
            </div>
          ))}
          {notes.length === 0 && <p className="text-sm text-paper/50">No notifications yet.</p>}
        </div>
      </div>
    </div>
  );
}

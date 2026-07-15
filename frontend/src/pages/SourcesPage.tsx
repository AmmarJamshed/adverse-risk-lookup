import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, RegulatorySource } from "../lib/api";

export default function SourcesPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [jurisdiction, setJurisdiction] = useState("UK");
  const [regulator, setRegulator] = useState("");

  const { data = [] } = useQuery({
    queryKey: ["sources"],
    queryFn: async () => (await api.get<RegulatorySource[]>("/sources")).data,
  });

  async function addSource(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/sources", { name, url, jurisdiction, regulator });
    setName("");
    setUrl("");
    setRegulator("");
    qc.invalidateQueries({ queryKey: ["sources"] });
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="arl-page-title">Regulatory Sources</h1>
        <p className="arl-page-sub">Watchlists feeding the horizon scan (FCA, FinCEN, EBA, SBP, Fed…)</p>
      </div>

      <form
        onSubmit={addSource}
        className="arl-panel grid gap-3 p-4 md:grid-cols-2 lg:grid-cols-5"
      >
        <input
          className="arl-input"
          placeholder="Source name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="arl-input"
          placeholder="Regulator"
          value={regulator}
          onChange={(e) => setRegulator(e.target.value)}
        />
        <select
          className="arl-input"
          value={jurisdiction}
          onChange={(e) => setJurisdiction(e.target.value)}
        >
          <option value="UK">UK</option>
          <option value="USA">USA</option>
          <option value="EU">EU</option>
          <option value="Pakistan">Pakistan</option>
        </select>
        <input
          className="arl-input"
          placeholder="https://…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
        />
        <button className="arl-btn" type="submit">
          Add source
        </button>
      </form>

      <div className="arl-table-wrap">
        <div className="divide-y divide-steel-100 dark:divide-navy-800">
          {data.map((s) => (
            <div key={s.id} className="grid gap-2 px-4 py-3 md:grid-cols-[1fr_100px_120px]">
              <div>
                <div className="font-medium text-navy-900 dark:text-white">{s.name}</div>
                <div className="truncate text-xs text-steel-500">{s.url}</div>
              </div>
              <div className="text-xs text-steel-600">
                {s.jurisdiction} · {s.regulator}
              </div>
              <div>
                <span className="arl-badge bg-brand-soft text-brand">{s.last_status || "—"}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

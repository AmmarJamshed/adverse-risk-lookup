import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, Article } from "../lib/api";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [country, setCountry] = useState("");
  const [severity, setSeverity] = useState("");
  const [submitted, setSubmitted] = useState({ q: "", country: "", severity: "" });

  const { data = [], isFetching } = useQuery({
    queryKey: ["search", submitted],
    queryFn: async () =>
      (
        await api.get<Article[]>("/articles", {
          params: {
            q: submitted.q || undefined,
            country: submitted.country || undefined,
            severity: submitted.severity || undefined,
            limit: 50,
          },
        })
      ).data,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Global Search</h1>
        <p className="text-sm text-paper/60">Search by risk, country, bank, language, severity, and more</p>
      </div>
      <form
        className="arl-panel grid gap-3 p-4 md:grid-cols-4"
        onSubmit={(e) => {
          e.preventDefault();
          setSubmitted({ q, country, severity });
        }}
      >
        <input className="arl-input md:col-span-2" placeholder="Keyword / bank / regulator / control" value={q} onChange={(e) => setQ(e.target.value)} />
        <input className="arl-input" placeholder="Country" value={country} onChange={(e) => setCountry(e.target.value)} />
        <select className="arl-input" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">Any severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button className="arl-btn md:col-span-4" type="submit">
          {isFetching ? "Searching…" : "Search"}
        </button>
      </form>
      <div className="space-y-2">
        {data.map((a) => (
          <Link key={a.id} to={`/articles/${a.id}`} className="arl-panel block p-4 text-sm hover:border-signal/30">
            <div className="font-medium">{a.title_en || a.title}</div>
            <div className="mt-1 text-xs text-paper/50">
              {a.country} · {a.severity} · {a.risk_category}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

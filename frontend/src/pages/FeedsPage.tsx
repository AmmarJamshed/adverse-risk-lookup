import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

type Feed = {
  id: string;
  name: string;
  url: string;
  category: string;
  country?: string;
  is_active: boolean;
  last_status?: string;
  success_count: number;
  failure_count: number;
};

export default function FeedsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const { data = [] } = useQuery({
    queryKey: ["feeds"],
    queryFn: async () => (await api.get<Feed[]>("/feeds")).data,
  });

  async function addFeed(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/feeds", { name, url, category: "financial" });
    setName("");
    setUrl("");
    qc.invalidateQueries({ queryKey: ["feeds"] });
  }

  async function fetchFeed(id: string) {
    await api.post(`/feeds/${id}/fetch`);
    qc.invalidateQueries({ queryKey: ["feeds"] });
  }

  async function collectNewsApi() {
    await api.post("/feeds/collect-newsapi");
    alert("NewsAPI collection started / completed");
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold">News Sources</h1>
          <p className="text-sm text-paper/60">Unlimited RSS feeds + NewsAPI integration</p>
        </div>
        <button type="button" className="arl-btn" onClick={collectNewsApi}>
          Collect from NewsAPI
        </button>
      </div>

      <form onSubmit={addFeed} className="arl-panel grid gap-3 p-4 md:grid-cols-3">
        <input className="arl-input" placeholder="Feed name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input className="arl-input" placeholder="https://…/feed.xml" value={url} onChange={(e) => setUrl(e.target.value)} required />
        <button className="arl-btn" type="submit">
          Add RSS Feed
        </button>
      </form>

      <div className="space-y-2">
        {data.map((f) => (
          <div key={f.id} className="arl-panel flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <div className="font-medium">{f.name}</div>
              <div className="text-xs text-paper/50">{f.url}</div>
              <div className="mt-1 text-[11px] text-paper/45">
                {f.category} · {f.country || "—"} · status {f.last_status || "never"} · ✓{f.success_count} ✗
                {f.failure_count}
              </div>
            </div>
            <button type="button" className="arl-btn-ghost" onClick={() => fetchFeed(f.id)}>
              Fetch now
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

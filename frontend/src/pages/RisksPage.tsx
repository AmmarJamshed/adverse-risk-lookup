import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

type Risk = {
  id: string;
  risk_id: string;
  name: string;
  description?: string;
  category?: string;
  owner?: string;
  department?: string;
  status: string;
};

export default function RisksPage() {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<{
    columns: string[];
    suggested_mapping: Record<string, string | null>;
    row_count: number;
  } | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const { data = [] } = useQuery({
    queryKey: ["risks"],
    queryFn: async () => (await api.get<Risk[]>("/risks")).data,
  });

  async function onPreview() {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await api.post("/risks/upload/preview", fd);
    setPreview(data);
    const cleaned: Record<string, string> = {};
    Object.entries(data.suggested_mapping || {}).forEach(([k, v]) => {
      if (v) cleaned[k] = String(v);
    });
    setMapping(cleaned);
  }

  async function onImport() {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("mapping", JSON.stringify(mapping));
    const { data } = await api.post("/risks/upload/import", fd);
    setMsg(`Imported ${data.created} new, updated ${data.updated}`);
    qc.invalidateQueries({ queryKey: ["risks"] });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Risk Register</h1>
        <p className="text-sm text-paper/60 light:text-ink-900/60">
          Upload CSV/Excel with intelligent column mapping for semantic matching
        </p>
      </div>

      <div className="arl-panel space-y-3 p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide">Upload Wizard</h2>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-sm"
        />
        <div className="flex gap-2">
          <button type="button" className="arl-btn" onClick={onPreview} disabled={!file}>
            Preview & Map Columns
          </button>
          <button type="button" className="arl-btn-ghost" onClick={onImport} disabled={!preview}>
            Import Risks
          </button>
        </div>
        {preview && (
          <div className="space-y-2 text-sm">
            <p>
              {preview.row_count} rows · columns: {preview.columns.join(", ")}
            </p>
            {Object.keys(preview.suggested_mapping).map((field) => (
              <div key={field} className="flex items-center gap-2">
                <label className="w-36 text-xs uppercase text-paper/50">{field}</label>
                <select
                  className="arl-input"
                  value={mapping[field] || ""}
                  onChange={(e) => setMapping({ ...mapping, [field]: e.target.value })}
                >
                  <option value="">— skip —</option>
                  {preview.columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}
        {msg && <p className="text-sm text-signal">{msg}</p>}
      </div>

      <div className="arl-panel overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-white/10 text-xs uppercase text-paper/50 light:border-ink-900/10">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Department</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.id} className="border-b border-white/5 light:border-ink-900/5">
                <td className="px-4 py-3 font-mono text-xs">{r.risk_id}</td>
                <td className="px-4 py-3">{r.name}</td>
                <td className="px-4 py-3">{r.category}</td>
                <td className="px-4 py-3">{r.owner}</td>
                <td className="px-4 py-3">{r.department}</td>
                <td className="px-4 py-3">{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

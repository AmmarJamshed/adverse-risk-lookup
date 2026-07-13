import { api } from "../lib/api";

export default function ReportsPage() {
  async function download(kind: "pdf" | "excel" | "word") {
    const res = await api.get(`/reports/${kind}`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download =
      kind === "pdf" ? "arl-report.pdf" : kind === "excel" ? "arl-report.xlsx" : "arl-report.docx";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Reports</h1>
        <p className="text-sm text-paper/60">
          Executive summaries, critical incidents, risk mapping, and trend packs
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="arl-panel p-6">
          <h2 className="font-display text-xl">PDF Management Report</h2>
          <p className="mt-2 text-sm text-paper/60">
            Includes executive summary, critical incidents, and category tables.
          </p>
          <button type="button" className="arl-btn mt-4" onClick={() => download("pdf")}>
            Download PDF
          </button>
        </div>
        <div className="arl-panel p-6">
          <h2 className="font-display text-xl">Excel Export</h2>
          <p className="mt-2 text-sm text-paper/60">
            Tabular export of relevant articles for audit and committee packs.
          </p>
          <button type="button" className="arl-btn mt-4" onClick={() => download("excel")}>
            Download Excel
          </button>
        </div>
        <div className="arl-panel p-6">
          <h2 className="font-display text-xl">Word Briefing</h2>
          <p className="mt-2 text-sm text-paper/60">
            Narrative management brief for risk committees and board packs.
          </p>
          <button type="button" className="arl-btn mt-4" onClick={() => download("word")}>
            Download Word
          </button>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { api } from "../lib/api";

const examples = [
  "Show today's cyber risks.",
  "Summarize AML news.",
  "What risks increased this week?",
  "Show fraud news in Pakistan.",
  "Generate executive summary.",
];

export default function AssistantPage() {
  const [question, setQuestion] = useState(examples[0]);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/assistant", { question });
      setAnswer(data.answer);
    } catch {
      setAnswer("Assistant unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">AI Assistant</h1>
        <p className="text-sm text-paper/60">Enterprise risk intelligence chatbot grounded in ARL context</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {examples.map((ex) => (
          <button key={ex} type="button" className="arl-btn-ghost text-xs" onClick={() => setQuestion(ex)}>
            {ex}
          </button>
        ))}
      </div>

      <form onSubmit={ask} className="arl-panel space-y-3 p-4">
        <textarea
          className="arl-input min-h-[100px]"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button className="arl-btn" type="submit" disabled={loading}>
          {loading ? "Analyzing…" : "Ask ARL"}
        </button>
      </form>

      {answer && (
        <div className="arl-panel animate-fade-up whitespace-pre-wrap p-4 text-sm leading-relaxed">
          {answer}
        </div>
      )}
    </div>
  );
}

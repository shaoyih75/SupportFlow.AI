"use client";

import { useParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { askAssistant } from "@/lib/api";
import type { AssistantAnswer } from "@/lib/types";

export default function AssistantPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AssistantAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await askAssistant(workspaceId, question.trim()));
    } catch {
      setError("The assistant is unavailable right now");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (question.trim()) ask();
  }

  return (
    <>
      <PageHeader
        title="AI Assistant"
        description="Ask questions about this workspace's documents. Answers cite their sources (mock for now)."
      />

      <form className="ask-form" onSubmit={handleSubmit}>
        <input
          className="input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder='Try "What is our refund policy?"'
          aria-label="Question"
        />
        <button className="button button-primary" type="submit" disabled={!question.trim() || loading}>
          Ask
        </button>
      </form>

      {loading && <LoadingState label="Thinking…" />}
      {error && <ErrorState message={error} onRetry={ask} />}
      {result && (
        <section className="card answer">
          <p>{result.answer}</p>
          {result.citations.length > 0 && (
            <>
              <p className="field-label">Sources</p>
              <ul>
                {result.citations.map((c) => (
                  <li key={c.documentId}>{c.documentTitle}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </>
  );
}

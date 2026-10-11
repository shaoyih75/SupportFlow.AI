"use client";

import { useState, type FormEvent } from "react";
import { ApiError, createTicket, type FieldErrors } from "@/lib/api";
import type { Ticket, TicketPriority } from "@/lib/types";

const PRIORITIES: TicketPriority[] = ["LOW", "MEDIUM", "HIGH"];

type TicketFormProps = {
  workspaceId: string;
  onCreated: (ticket: Ticket) => void;
};

export const TICKET_SUBJECT_INPUT_ID = "ticket-subject";

export function TicketForm({ workspaceId, onCreated }: TicketFormProps) {
  const [subject, setSubject] = useState("");
  const [priority, setPriority] = useState<TicketPriority>("MEDIUM");
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setFieldErrors({});
    setFormError(null);
    try {
      // No client-side length check on purpose: let FastAPI's 422 drive the field errors.
      const ticket = await createTicket(workspaceId, { subject, priority });
      setSubject("");
      onCreated(ticket);
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setFieldErrors(err.fieldErrors);
      } else {
        setFormError(err instanceof Error ? err.message : "Failed to create ticket");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card ticket-form" onSubmit={handleSubmit} noValidate>
      <div className="form-row">
        <div className="form-field grow">
          <label className="field-label" htmlFor={TICKET_SUBJECT_INPUT_ID}>
            Subject
          </label>
          <input
            id={TICKET_SUBJECT_INPUT_ID}
            className={fieldErrors.subject ? "input input-invalid" : "input"}
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Describe the customer's problem"
            aria-invalid={Boolean(fieldErrors.subject)}
          />
          {fieldErrors.subject && <p className="field-error">{fieldErrors.subject}</p>}
        </div>
        <div className="form-field">
          <label className="field-label" htmlFor="ticket-priority">
            Priority
          </label>
          <select
            id="ticket-priority"
            className="select"
            value={priority}
            onChange={(e) => setPriority(e.target.value as TicketPriority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          {fieldErrors.priority && <p className="field-error">{fieldErrors.priority}</p>}
        </div>
        <button className="button button-primary" type="submit" disabled={submitting}>
          {submitting ? "Creating…" : "Create ticket"}
        </button>
      </div>
      {formError && <p className="field-error">{formError}</p>}
    </form>
  );
}

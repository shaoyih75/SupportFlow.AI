"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { ApiError, describeError, login, register, type FieldErrors } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";

// Same limits as the backend's RegisterRequest. Checking here is only for quick feedback:
// the backend validates again and answers 422 if anything slips through.
const NAME_MAX = 100;
const PASSWORD_MIN = 8;
const PASSWORD_MAX = 72;

type Form = { name: string; email: string; password: string; confirm: string };

function validate(form: Form): FieldErrors {
  const errors: FieldErrors = {};
  if (!form.name.trim()) errors.name = "Enter your name";
  else if (form.name.trim().length > NAME_MAX) errors.name = `At most ${NAME_MAX} characters`;
  if (!/^\S+@\S+\.\S+$/.test(form.email)) errors.email = "Enter a valid email address";
  if (form.password.length < PASSWORD_MIN) errors.password = `At least ${PASSWORD_MIN} characters`;
  else if (form.password.length > PASSWORD_MAX) errors.password = `At most ${PASSWORD_MAX} characters`;
  if (form.confirm !== form.password) errors.confirm = "Passwords do not match";
  return errors;
}

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState<Form>({ name: "", email: "", password: "", confirm: "" });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const update = (field: keyof Form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const errors = validate(form);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await register(form.name.trim(), form.email, form.password);
      // Registering does not hand out a token: log in with the same credentials.
      const token = await login(form.email, form.password);
      setAccessToken(token);
      router.replace("/workspaces");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFieldErrors({ email: "This email is already registered. Log in instead?" });
      } else if (err instanceof ApiError && err.status === 422) {
        setFieldErrors(err.fieldErrors); // keys match our inputs: name, email, password
      } else {
        setError(describeError(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  // One input + its error message; the ids double as the backend's field names.
  function field(id: keyof Form, label: string, type: string, autoComplete: string) {
    return (
      <div className="form-field">
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
        <input
          id={id}
          className={`input${fieldErrors[id] ? " input-invalid" : ""}`}
          type={type}
          autoComplete={autoComplete}
          value={form[id]}
          onChange={update(id)}
          aria-invalid={Boolean(fieldErrors[id])}
          required
        />
        {fieldErrors[id] && <p className="field-error">{fieldErrors[id]}</p>}
      </div>
    );
  }

  return (
    <main className="login">
      <form className="card login-card" onSubmit={handleSubmit} noValidate>
        <div className="brand">
          <span className="brand-mark">S</span> SupportFlow<span className="brand-ai">.AI</span>
        </div>
        <h1>Create an account</h1>

        {field("name", "Name", "text", "name")}
        {field("email", "Email", "email", "username")}
        {field("password", `Password (${PASSWORD_MIN}–${PASSWORD_MAX} characters)`, "password", "new-password")}
        {field("confirm", "Confirm password", "password", "new-password")}

        {error && <p className="field-error">{error}</p>}
        <button className="button button-primary" type="submit" disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </button>

        <p className="muted auth-switch">
          Already have an account? <Link href="/login">Log in</Link>
        </p>
      </form>
    </main>
  );
}

import { LockKeyhole } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { authApi, getApiError } from "../api/client";
import AuthShell from "../components/AuthShell";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PasswordInput from "../components/PasswordInput";
import { Field } from "./Login";

export default function ResetPassword() {
  const [params] = useSearchParams(); const [form, setForm] = useState({ password: "", confirmPassword: "" }); const [error, setError] = useState(""); const [success, setSuccess] = useState(false); const [loading, setLoading] = useState(false); const token = params.get("token") || "";
  async function handleSubmit(event) { event.preventDefault(); setError(""); if (form.password !== form.confirmPassword) { setError("Passwords do not match."); return; } setLoading(true); try { await authApi.resetPassword({ token, password: form.password }); setSuccess(true); } catch (err) { setError(getApiError(err, "Unable to reset your password.")); } finally { setLoading(false); } }
  return <AuthShell eyebrow="Secure recovery" title="Choose a new password" description="Use at least eight characters with a letter and a number.">{success ? <div className="space-y-5"><div className="rounded-xl border border-teal-200 bg-teal-50 p-4 text-sm text-teal-800 dark:border-teal-400/20 dark:bg-teal-400/10 dark:text-teal-200">Your password has been reset successfully.</div><Link className="btn-primary w-full" to="/login">Continue to sign in</Link></div> : <form onSubmit={handleSubmit} className="space-y-5"><ErrorBanner message={!token ? "This reset link is invalid." : error} /><Field label="New password" icon={LockKeyhole}><PasswordInput className="input pl-11" autoComplete="new-password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></Field><Field label="Confirm new password" icon={LockKeyhole}><PasswordInput className="input pl-11" autoComplete="new-password" minLength={8} value={form.confirmPassword} onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })} required /></Field><button className="btn-primary w-full" disabled={loading || !token}>{loading ? <LoadingSpinner label="Updating password" /> : "Update password"}</button></form>}</AuthShell>;
}

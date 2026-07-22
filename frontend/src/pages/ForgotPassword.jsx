import { ArrowLeft, Mail, Send } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { authApi, getApiError } from "../api/client";
import AuthShell from "../components/AuthShell";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import { Field } from "./Login";

export default function ForgotPassword() {
  const [email, setEmail] = useState(""); const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [loading, setLoading] = useState(false);
  async function handleSubmit(event) { event.preventDefault(); setError(""); setMessage(""); setLoading(true); try { const response = await authApi.forgotPassword({ email }); setMessage(response.data.message); } catch (err) { setError(getApiError(err, "Unable to request a reset link.")); } finally { setLoading(false); } }
  return <AuthShell eyebrow="Account recovery" title="Reset your password" description="Enter your registered email and we’ll send you a secure, one-hour reset link."><form onSubmit={handleSubmit} className="space-y-5"><ErrorBanner message={error} />{message ? <div className="rounded-xl border border-teal-200 bg-teal-50 p-4 text-sm text-teal-800 dark:border-teal-400/20 dark:bg-teal-400/10 dark:text-teal-200">{message}</div> : null}<Field label="Email address" icon={Mail}><input className="input pl-11" type="email" autoComplete="email" placeholder="name@firm.com" value={email} onChange={(e) => setEmail(e.target.value)} required /></Field><button className="btn-primary w-full" disabled={loading}>{loading ? <LoadingSpinner label="Sending link" /> : <><Send className="h-4 w-4" /> Send reset link</>}</button></form><Link className="btn-quiet mx-auto mt-6 w-fit" to="/login"><ArrowLeft className="h-4 w-4" /> Back to sign in</Link></AuthShell>;
}

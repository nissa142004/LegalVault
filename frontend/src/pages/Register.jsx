import { LockKeyhole, Mail, User, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import AuthShell from "../components/AuthShell";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { Field } from "./Login";

export default function Register() {
  const navigate = useNavigate();
  const { booting, isAuthenticated, register } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (booting) return <main className="grid min-h-screen place-items-center"><LoadingSpinner label="Checking session" /></main>;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event) {
    event.preventDefault(); setError(""); setLoading(true);
    try { await register(form); navigate("/dashboard"); } catch (err) { setError(err.message); } finally { setLoading(false); }
  }
  return (
    <AuthShell eyebrow="Get started" title="Create your LegalVault" description="Set up a secure workspace for your legal documents in just a moment.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <ErrorBanner message={error} />
        <Field label="Full name" icon={User}><input className="input pl-11" autoComplete="name" placeholder="Your full name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></Field>
        <Field label="Email address" icon={Mail}><input className="input pl-11" type="email" autoComplete="email" placeholder="name@firm.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></Field>
        <Field label="Password" icon={LockKeyhole}><input className="input pl-11" type="password" autoComplete="new-password" placeholder="At least 8 characters" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></Field>
        <p className="text-xs leading-5 text-slate-400">By creating an account, you agree to use LegalVault responsibly for authorized documents.</p>
        <button className="btn-primary w-full" type="submit" disabled={loading}>{loading ? <LoadingSpinner label="Creating account" /> : <><UserPlus className="h-4 w-4" /> Create account</>}</button>
      </form>
      <p className="mt-7 text-center text-sm text-slate-500 dark:text-slate-400">Already have an account? <Link className="font-bold text-teal-600 hover:text-teal-500 dark:text-teal-300" to="/login">Sign in</Link></p>
    </AuthShell>
  );
}

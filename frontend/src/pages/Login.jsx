import { LockKeyhole, Mail } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import AuthShell from "../components/AuthShell";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const location = useLocation();
  const navigate = useNavigate();
  const { booting, isAuthenticated, login } = useAuth();
  const [authMessage] = useState(() => location.state?.authMessage || "");
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!location.state?.authMessage) return;

    const { authMessage: _authMessage, ...remainingState } = location.state;
    navigate(location.pathname, {
      replace: true,
      state: Object.keys(remainingState).length ? remainingState : null,
    });
  }, [location.pathname, location.state, navigate]);

  if (booting) return <main className="grid min-h-screen place-items-center"><LoadingSpinner label="Checking session" /></main>;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(event) {
    event.preventDefault(); setError(""); setLoading(true);
    try { await login(form); navigate("/dashboard", { state: { successMessage: "You have signed in successfully." } }); } catch (err) { setError(err.message); } finally { setLoading(false); }
  }

  return (
    <AuthShell eyebrow="Welcome back" title="Sign in to your workspace" description="Access your documents, insights, and legal research in one place.">
      <form onSubmit={handleSubmit} className="space-y-5">
        <ErrorBanner message={error || authMessage} />
        <Field label="Email address" icon={Mail}><input className="input pl-11" type="email" autoComplete="email" placeholder="name@firm.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></Field>
        <Field label="Password" icon={LockKeyhole}><PasswordInput className="input pl-11" autoComplete="current-password" placeholder="Enter your password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></Field>
        <div className="-mt-2 text-right"><Link className="text-sm font-semibold text-teal-600 hover:text-teal-500 dark:text-teal-300" to="/forgot-password">Forgot password?</Link></div>
        <button className="btn-primary w-full" type="submit" disabled={loading}>{loading ? <LoadingSpinner label="Signing in" /> : <><LockKeyhole className="h-4 w-4" /> Sign in securely</>}</button>
      </form>
      <p className="mt-7 text-center text-sm text-slate-500 dark:text-slate-400">New to LegalVault? <Link className="font-bold text-teal-600 hover:text-teal-500 dark:text-teal-300" to="/register">Create an account</Link></p>
    </AuthShell>
  );
}

export function Field({ label, icon: Icon, children }) {
  return <label className="block"><span className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">{label}</span><span className="relative block"><Icon className="pointer-events-none absolute left-4 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-slate-400" />{children}</span></label>;
}

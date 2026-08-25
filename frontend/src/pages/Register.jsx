import { BadgeCheck, BriefcaseBusiness, Building2, Globe2, LockKeyhole, Mail, Phone, User, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import AuthShell from "../components/AuthShell";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";
import { Field } from "./Login";

const initialForm = { name: "", email: "", phone: "", organization: "", job_title: "", jurisdiction: "", professional_id: "", password: "", confirmPassword: "" };

export default function Register() {
  const navigate = useNavigate(); const { booting, isAuthenticated, register } = useAuth();
  const [form, setForm] = useState(initialForm); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  if (booting) return <main className="grid min-h-screen place-items-center"><LoadingSpinner label="Checking session" /></main>;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });
  async function handleSubmit(event) { event.preventDefault(); setError(""); if (form.password !== form.confirmPassword) { setError("Passwords do not match."); return; } setLoading(true); try { const { confirmPassword, ...payload } = form; await register(payload); navigate("/dashboard", { state: { successMessage: "Your account was created successfully." } }); } catch (err) { setError(err.message); } finally { setLoading(false); } }

  return <AuthShell wide eyebrow="Professional registration" title="Create your LegalVault" description="Build your secure professional profile and start organizing legal knowledge.">
    <form onSubmit={handleSubmit} className="space-y-5"><ErrorBanner message={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Full name" icon={User}><input className="input pl-11" autoComplete="name" placeholder="Your full name" value={form.name} onChange={update("name")} required /></Field>
        <Field label="Professional email" icon={Mail}><input className="input pl-11" type="email" autoComplete="email" placeholder="name@firm.com" value={form.email} onChange={update("email")} required /></Field>
        <Field label="Phone number" icon={Phone}><input className="input pl-11" type="tel" autoComplete="tel" placeholder="+94 77 123 4567" value={form.phone} onChange={update("phone")} /></Field>
        <Field label="Organization / firm" icon={Building2}><input className="input pl-11" autoComplete="organization" placeholder="Law firm or organization" value={form.organization} onChange={update("organization")} /></Field>
        <Field label="Job title" icon={BriefcaseBusiness}><input className="input pl-11" autoComplete="organization-title" placeholder="Attorney, paralegal, student…" value={form.job_title} onChange={update("job_title")} /></Field>
        <Field label="Jurisdiction" icon={Globe2}><input className="input pl-11" placeholder="Country, state, or province" value={form.jurisdiction} onChange={update("jurisdiction")} /></Field>
        <Field label="Bar / professional ID" icon={BadgeCheck}><input className="input pl-11" placeholder="Optional registration number" value={form.professional_id} onChange={update("professional_id")} /></Field>
        <div />
        <Field label="Password" icon={LockKeyhole}><PasswordInput className="input pl-11" autoComplete="new-password" placeholder="At least 8 characters" minLength={8} value={form.password} onChange={update("password")} required /></Field>
        <Field label="Confirm password" icon={LockKeyhole}><PasswordInput className="input pl-11" autoComplete="new-password" placeholder="Repeat your password" minLength={8} value={form.confirmPassword} onChange={update("confirmPassword")} required /></Field>
      </div>
      <p className="text-xs leading-5 text-slate-400">Use at least eight characters with a letter and number. By registering, you agree to use LegalVault only for authorized documents.</p>
      <button className="btn-primary w-full" type="submit" disabled={loading}>{loading ? <LoadingSpinner label="Creating account" /> : <><UserPlus className="h-4 w-4" /> Create account</>}</button>
    </form>
    <p className="mt-7 text-center text-sm text-slate-500 dark:text-slate-400">Already have an account? <Link className="font-bold text-teal-600 hover:text-teal-500 dark:text-teal-300" to="/login">Sign in</Link></p>
  </AuthShell>;
}

import { motion } from "framer-motion";
import { LockKeyhole } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import ThemeToggle from "../components/ThemeToggle";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { booting, isAuthenticated, login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (booting) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <LoadingSpinner label="Checking session" />
      </main>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(form);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthPage title="Welcome back" subtitle="Sign in to continue your legal document work.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <ErrorBanner message={error} />
        <input
          className="input"
          type="email"
          placeholder="Email address"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(event) => setForm({ ...form, password: event.target.value })}
          required
        />
        <button className="btn-primary w-full" type="submit" disabled={loading}>
          {loading ? <LoadingSpinner label="Signing in" /> : <LockKeyhole className="h-4 w-4" />}
          {!loading ? "Login" : null}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        New to LegalVault?{" "}
        <Link className="font-semibold text-vault-accent hover:text-cyan-300" to="/register">
          Create an account
        </Link>
      </p>
    </AuthPage>
  );
}

function AuthPage({ title, subtitle, children }) {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10 text-slate-900 dark:text-slate-100">
      <div className="fixed right-4 top-4">
        <ThemeToggle compact />
      </div>
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="panel w-full max-w-md rounded-lg p-6 sm:p-8"
      >
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase text-vault-accent">
            LegalVault
          </p>
          <h1 className="mt-3 text-3xl font-bold text-slate-950 dark:text-white">{title}</h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
        </div>
        {children}
      </motion.section>
    </main>
  );
}

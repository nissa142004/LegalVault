import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  FileSearch,
  Files,
  LayoutDashboard,
  LogOut,
  Menu,
  UploadCloud,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, useLocation } from "react-router-dom";

import LoadingSpinner from "./components/LoadingSpinner";
import ProductLogo from "./components/ProductLogo";
import ThemeToggle from "./components/ThemeToggle";
import { useAuth } from "./context/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard", description: "Workspace overview", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", description: "Add a legal document", icon: UploadCloud },
  { to: "/search", label: "Search", description: "Find clauses and matters", icon: FileSearch },
  { to: "/evaluation", label: "Evaluation", description: "Model quality metrics", icon: BarChart3 },
];

export default function App() {
  const location = useLocation();
  const { booting, isAuthenticated, logout, user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => setMobileMenuOpen(false), [location.pathname]);

  if (booting) {
    return (
      <main className="grid min-h-screen place-items-center">
        <div className="flex flex-col items-center gap-4">
          <ProductLogo className="h-20 w-20" />
          <LoadingSpinner label="Opening your secure workspace" />
        </div>
      </main>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen text-slate-900 dark:text-slate-100">
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200/70 bg-white/80 px-4 backdrop-blur-xl dark:border-white/[0.08] dark:bg-vault-950/80 lg:hidden">
        <Brand compact />
        <div className="flex items-center gap-2">
          <ThemeToggle compact />
          <button
            className="icon-button"
            onClick={() => setMobileMenuOpen((open) => !open)}
            aria-label="Toggle navigation"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      <AnimatePresence>
        {mobileMenuOpen ? (
          <>
            <motion.button
              aria-label="Close navigation"
              className="fixed inset-0 z-30 bg-slate-950/35 backdrop-blur-sm lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-40 w-[min(84vw,20rem)] border-r border-slate-200 bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-vault-900 lg:hidden"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 280 }}
            >
              <SidebarContent user={user} logout={logout} />
            </motion.aside>
          </>
        ) : null}
      </AnimatePresence>

      <aside className="fixed inset-y-0 left-0 z-20 hidden w-72 border-r border-slate-200/70 bg-white/75 p-5 backdrop-blur-xl dark:border-white/[0.08] dark:bg-vault-950/75 lg:block">
        <SidebarContent user={user} logout={logout} desktop />
      </aside>

      <main className="min-h-[calc(100vh-4rem)] lg:ml-72 lg:min-h-screen">
        <div className="mx-auto w-full max-w-[90rem] px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

function SidebarContent({ user, logout, desktop = false }) {
  return (
    <div className="flex h-full flex-col">
      <Brand />
      <div className="my-7 h-px bg-slate-200/80 dark:bg-white/[0.08]" />
      <p className="mb-3 px-3 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
        Workspace
      </p>
      <nav className="space-y-1.5">
        {navItems.map(({ to, label, description, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}
          >
            <span className="nav-icon"><Icon className="h-[1.15rem] w-[1.15rem]" /></span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold">{label}</span>
              <span className="block truncate text-[0.7rem] opacity-60">{description}</span>
            </span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-6">
        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-3.5 dark:border-white/[0.08] dark:bg-white/[0.035]">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 text-sm font-bold text-vault-950 shadow-sm">
              {(user?.name || "U").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">{user?.name}</p>
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            {desktop ? <ThemeToggle compact /> : null}
            <button onClick={logout} className="btn-quiet flex-1">
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Brand({ compact = false }) {
  return (
    <div className="flex items-center gap-3">
      <ProductLogo className={compact ? "h-10 w-10" : "h-12 w-12"} decorative />
      <div>
        <p className="flex items-center gap-1.5 text-base font-extrabold tracking-tight text-slate-950 dark:text-white">
          LegalVault {!compact && <Files className="h-3.5 w-3.5 text-vault-accent" />}
        </p>
        {!compact ? <p className="text-[0.68rem] text-slate-500 dark:text-slate-400">Intelligent document workspace</p> : null}
      </div>
    </div>
  );
}

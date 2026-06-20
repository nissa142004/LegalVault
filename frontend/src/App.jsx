import { AnimatePresence, motion } from "framer-motion";
import { FileSearch, FileText, LayoutDashboard, LogOut, UploadCloud } from "lucide-react";
import { NavLink, Navigate, Outlet, useLocation } from "react-router-dom";

import LoadingSpinner from "./components/LoadingSpinner";
import ThemeToggle from "./components/ThemeToggle";
import { useAuth } from "./context/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", icon: UploadCloud },
  { to: "/search", label: "Search", icon: FileSearch },
];

export default function App() {
  const location = useLocation();
  const { booting, isAuthenticated, logout, user } = useAuth();

  if (booting) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <LoadingSpinner label="Opening LegalVault" />
      </main>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen text-slate-900 dark:text-slate-100">
      <aside className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white/95 px-3 py-2 backdrop-blur dark:border-white/10 dark:bg-vault-950/95 lg:inset-y-0 lg:left-0 lg:right-auto lg:w-72 lg:border-r lg:border-t-0 lg:p-5">
        <div className="hidden lg:block">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-vault-accent text-vault-950">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <p className="text-lg font-bold">LegalVault</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Intelligent legal archive</p>
            </div>
          </div>
        </div>

        <nav className="grid grid-cols-4 gap-2 lg:grid-cols-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-medium transition lg:justify-start",
                  isActive
                    ? "bg-vault-accent text-vault-950"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-white/[0.06] dark:hover:text-white",
                ].join(" ")
              }
            >
              <item.icon className="h-5 w-5" />
              <span className="hidden sm:inline">{item.label}</span>
            </NavLink>
          ))}
          <div className="flex items-center justify-center lg:hidden">
            <ThemeToggle compact />
          </div>
        </nav>

        <div className="mt-auto hidden pt-8 lg:block">
          <div className="rounded-lg border border-slate-200 bg-white/70 p-4 dark:border-white/10 dark:bg-white/[0.04]">
            <p className="text-sm font-semibold">{user?.name}</p>
            <p className="mt-1 break-all text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
            <div className="mt-4 flex items-center justify-between gap-3">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Theme</span>
              <ThemeToggle compact />
            </div>
            <button onClick={logout} className="btn-secondary mt-4 w-full">
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <main className="min-h-screen pb-24 lg:ml-72 lg:pb-0">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

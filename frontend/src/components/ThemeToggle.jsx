import { motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";

import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle({ compact = false }) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="relative inline-flex h-9 w-[4.25rem] items-center rounded-xl border border-slate-200 bg-slate-100 p-1 text-slate-600 transition dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300"
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
    >
      <motion.span className="absolute h-7 w-7 rounded-lg bg-white shadow-sm dark:bg-teal-400" animate={{ x: isDark ? 31 : 0 }} transition={{ type: "spring", stiffness: 420, damping: 30 }} />
      <span className="relative z-10 grid h-7 w-7 place-items-center"><Sun className="h-3.5 w-3.5" /></span>
      <span className="relative z-10 ml-1 grid h-7 w-7 place-items-center"><Moon className="h-3.5 w-3.5" /></span>
      {!compact ? (
        <span className="sr-only">{isDark ? "Dark theme active" : "Light theme active"}</span>
      ) : null}
    </button>
  );
}

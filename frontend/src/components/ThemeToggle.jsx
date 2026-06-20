import { Moon, Sun } from "lucide-react";

import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle({ compact = false }) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={[
        "inline-flex items-center rounded-full border border-slate-200 bg-white p-1 text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.06] dark:text-slate-200 dark:hover:bg-white/[0.1]",
        compact ? "gap-1" : "gap-2",
      ].join(" ")}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
    >
      <span
        className={[
          "flex h-7 w-7 items-center justify-center rounded-full transition",
          !isDark ? "bg-vault-accent text-vault-950" : "text-slate-500 dark:text-slate-400",
        ].join(" ")}
      >
        <Sun className="h-4 w-4" />
      </span>
      <span
        className={[
          "flex h-7 w-7 items-center justify-center rounded-full transition",
          isDark ? "bg-vault-accent text-vault-950" : "text-slate-500 dark:text-slate-400",
        ].join(" ")}
      >
        <Moon className="h-4 w-4" />
      </span>
      {!compact ? (
        <span className="sr-only">{isDark ? "Dark theme active" : "Light theme active"}</span>
      ) : null}
    </button>
  );
}

import { motion } from "framer-motion";
import { CheckCircle2, Scale, ShieldCheck, Sparkles } from "lucide-react";

import ThemeToggle from "./ThemeToggle";

const benefits = [
  "Secure legal document workspace",
  "Intelligent search and summaries",
  "Fast extraction from PDF and DOCX",
];

export default function AuthShell({ eyebrow, title, description, children }) {
  return (
    <main className="grid min-h-screen text-slate-900 dark:text-slate-100 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden border-r border-slate-200/70 bg-slate-950 p-12 text-white dark:border-white/[0.08] lg:flex lg:flex-col lg:justify-between xl:p-16">
        <div className="absolute -left-24 top-1/4 h-80 w-80 rounded-full bg-teal-400/10 blur-3xl" />
        <div className="absolute -right-20 bottom-0 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 text-vault-950"><Scale className="h-5 w-5" /></div>
          <div><p className="text-lg font-extrabold">LegalVault</p><p className="text-xs text-slate-400">Intelligent document workspace</p></div>
        </div>
        <motion.div className="relative max-w-xl" initial={{ opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.55 }}>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-teal-300/15 bg-teal-300/10 px-3 py-1.5 text-xs font-semibold text-teal-200"><Sparkles className="h-3.5 w-3.5" /> A smarter legal archive</div>
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight xl:text-5xl">Your legal knowledge,<br /><span className="text-teal-300">organized and accessible.</span></h2>
          <p className="mt-5 max-w-lg text-base leading-7 text-slate-400">Turn dense legal files into searchable, structured knowledge while keeping your workflow simple.</p>
          <div className="mt-9 space-y-3">
            {benefits.map((benefit) => <div key={benefit} className="flex items-center gap-3 text-sm text-slate-300"><CheckCircle2 className="h-4 w-4 text-teal-300" />{benefit}</div>)}
          </div>
        </motion.div>
        <div className="relative flex items-center gap-2 text-xs text-slate-500"><ShieldCheck className="h-4 w-4" /> Built for focused, professional legal work</div>
      </section>

      <section className="relative flex min-h-screen items-center justify-center px-4 py-12 sm:px-8">
        <div className="absolute right-4 top-4 sm:right-7 sm:top-6"><ThemeToggle compact /></div>
        <motion.div className="w-full max-w-md" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}>
          <div className="mb-8 flex items-center gap-3 lg:hidden"><div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 text-vault-950"><Scale className="h-5 w-5" /></div><span className="font-extrabold">LegalVault</span></div>
          <p className="eyebrow">{eyebrow}</p>
          <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white sm:text-4xl">{title}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p>
          <div className="mt-8">{children}</div>
        </motion.div>
      </section>
    </main>
  );
}

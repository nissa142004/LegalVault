import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BrainCircuit,
  Clock3,
  FileCheck2,
  Files,
  RefreshCw,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { analyticsApi, getApiError } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

const CATEGORY_COLORS = ["#2dd4bf", "#38bdf8", "#818cf8", "#f59e0b", "#f472b6", "#94a3b8"];
const REFRESH_INTERVAL_MS = 30_000;

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadAnalytics = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setRefreshing(true);
    try {
      const response = await analyticsApi.dashboard();
      setData(response.data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load dashboard analytics."));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics({ silent: true });
    const interval = window.setInterval(() => loadAnalytics({ silent: true }), REFRESH_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [loadAnalytics]);

  const updatedAt = data?.generated_at
    ? new Date(data.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "—";

  if (loading) {
    return <div className="panel grid min-h-[28rem] place-items-center rounded-2xl"><LoadingSpinner label="Building live analytics" /></div>;
  }

  return (
    <>
      <PageHeader
        eyebrow="Live workspace"
        title="Analytics dashboard"
        description="A real-time view of your legal archive, document mix, and AI processing workflow."
        action={<div className="flex items-center gap-2"><span className="hidden text-xs text-slate-400 sm:block">Updated {updatedAt}</span><button className="btn-secondary" onClick={() => loadAnalytics()} disabled={refreshing}><RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} /> Refresh</button><Link className="btn-primary" to="/upload"><UploadCloud className="h-4 w-4" /> Upload</Link></div>}
      />

      <ErrorBanner message={error} />

      <motion.div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.06 } } }}>
        <MetricCard icon={Files} label="Total documents" value={data?.total_documents || 0} note="In your secure vault" tone="teal" />
        <MetricCard icon={FileCheck2} label="Text extracted" value={data?.processing?.text_extracted || 0} note={`${percent(data?.processing?.text_extracted, data?.total_documents)}% searchable`} tone="sky" />
        <MetricCard icon={BrainCircuit} label="Summaries generated" value={data?.processing?.ai_processed || 0} note={`${data?.processing?.completion_rate || 0}% completion rate`} tone="indigo" />
        <MetricCard icon={Clock3} label="Documents for review" value={(data?.governance?.needs_review || 0) + (data?.governance?.in_review || 0)} note={`${data?.governance?.privileged || 0} privileged records`} tone="amber" />
      </motion.div>

      {data?.total_documents === 0 ? (
        <div className="mt-6"><EmptyState title="Your analytics will appear here" description="Upload your first PDF or DOCX document to start building your live workspace overview." action={<Link className="btn-primary" to="/upload"><UploadCloud className="h-4 w-4" /> Upload document</Link>} /></div>
      ) : (
        <>
          <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <ChartPanel title="Category distribution" description="Documents classified by the LegalVault ML model">
              <CategoryBars categories={data?.categories || []} />
            </ChartPanel>
            <ChartPanel title="Document mix" description="Share of your vault by legal category">
              <CategoryPie categories={data?.categories || []} total={data?.total_documents || 0} />
            </ChartPanel>
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
            <ChartPanel title="Upload activity" description="Documents added over the last 7 days">
              <UploadBars values={data?.uploads_by_day || []} />
            </ChartPanel>
            <RecentUploads documents={data?.recent_uploads || []} />
          </div>
        </>
      )}
    </>
  );
}

function MetricCard({ icon: Icon, label, value, note, tone }) {
  const tones = {
    teal: "bg-teal-400/10 text-teal-600 dark:text-teal-300",
    sky: "bg-sky-400/10 text-sky-600 dark:text-sky-300",
    indigo: "bg-indigo-400/10 text-indigo-600 dark:text-indigo-300",
    amber: "bg-amber-400/10 text-amber-600 dark:text-amber-300",
  };
  return <motion.article variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } }} className="panel rounded-2xl p-5"><div className="flex items-start justify-between"><div className={`grid h-11 w-11 place-items-center rounded-xl ${tones[tone]}`}><Icon className="h-5 w-5" /></div><Sparkles className="h-4 w-4 text-slate-300 dark:text-slate-600" /></div><p className="mt-5 text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">{value}</p><p className="mt-1 text-sm font-semibold text-slate-700 dark:text-slate-200">{label}</p><p className="mt-1 text-xs text-slate-400">{note}</p></motion.article>;
}

function ChartPanel({ title, description, children }) {
  return <section className="panel rounded-2xl p-5 sm:p-6"><div><h2 className="font-bold text-slate-950 dark:text-white">{title}</h2><p className="mt-1 text-xs text-slate-400">{description}</p></div><div className="mt-6">{children}</div></section>;
}

function CategoryBars({ categories }) {
  const max = Math.max(...categories.map((item) => item.count), 1);
  return <div className="space-y-4">{categories.map((item, index) => <div key={item.category}><div className="mb-1.5 flex items-center justify-between text-xs"><span className="font-semibold text-slate-600 dark:text-slate-300">{item.category}</span><span className="text-slate-400">{item.count} · {item.percentage}%</span></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100 dark:bg-white/[0.06]"><motion.div className="h-full rounded-full" style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }} initial={{ width: 0 }} animate={{ width: `${(item.count / max) * 100}%` }} transition={{ duration: 0.65, delay: index * 0.07 }} /></div></div>)}</div>;
}

function CategoryPie({ categories, total }) {
  const gradient = useMemo(() => {
    let cursor = 0;
    const slices = categories.map((item, index) => {
      const start = cursor; cursor += item.percentage;
      return `${CATEGORY_COLORS[index % CATEGORY_COLORS.length]} ${start}% ${cursor}%`;
    });
    return `conic-gradient(${slices.join(", ")})`;
  }, [categories]);
  return <div className="flex flex-col items-center gap-7 sm:flex-row sm:justify-center"><div className="relative h-44 w-44 flex-none rounded-full shadow-inner" style={{ background: gradient }}><div className="absolute inset-[22%] grid place-items-center rounded-full bg-white shadow-sm dark:bg-[#0d131c]"><div className="text-center"><p className="text-2xl font-extrabold text-slate-950 dark:text-white">{total}</p><p className="text-[0.65rem] uppercase tracking-wider text-slate-400">Documents</p></div></div></div><div className="grid w-full gap-2">{categories.map((item, index) => <div key={item.category} className="flex items-center justify-between gap-5 text-xs"><span className="flex items-center gap-2 text-slate-600 dark:text-slate-300"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }} />{item.category}</span><span className="font-semibold text-slate-400">{item.percentage}%</span></div>)}</div></div>;
}

function UploadBars({ values }) {
  const max = Math.max(...values.map((item) => item.count), 1);
  return <div className="flex h-44 items-end gap-2 sm:gap-3">{values.map((item) => { const day = new Date(`${item.date}T00:00:00`).toLocaleDateString([], { weekday: "short" }); return <div key={item.date} className="flex h-full flex-1 flex-col items-center justify-end gap-2"><span className="text-[0.65rem] font-bold text-slate-400">{item.count || ""}</span><div className="flex h-[7.5rem] w-full items-end overflow-hidden rounded-lg bg-slate-100 dark:bg-white/[0.05]"><motion.div className="w-full rounded-lg bg-gradient-to-t from-teal-500 to-cyan-300" initial={{ height: 0 }} animate={{ height: `${item.count ? Math.max((item.count / max) * 100, 8) : 0}%` }} transition={{ duration: 0.55 }} /></div><span className="text-[0.65rem] text-slate-400">{day}</span></div>; })}</div>;
}

function RecentUploads({ documents }) {
  return <section className="panel overflow-hidden rounded-2xl"><div className="flex items-center justify-between border-b border-slate-200/70 p-5 dark:border-white/[0.07] sm:px-6"><div><h2 className="font-bold text-slate-950 dark:text-white">Recent uploads</h2><p className="mt-1 text-xs text-slate-400">Your latest additions</p></div><Link to="/search" className="btn-quiet">Browse all <ArrowUpRight className="h-3.5 w-3.5" /></Link></div><div className="divide-y divide-slate-200/70 dark:divide-white/[0.07]">{documents.map((document, index) => <Link key={document.id} to={`/documents/${document.id}`} className="flex items-center gap-3 px-5 py-3.5 transition hover:bg-slate-50 dark:hover:bg-white/[0.03] sm:px-6"><div className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-slate-100 text-teal-600 dark:bg-white/[0.05] dark:text-teal-300"><Files className="h-4 w-4" /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">{document.filename}</p><p className="mt-0.5 text-[0.68rem] text-slate-400">{new Date(document.upload_date).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}</p></div><span className="hidden rounded-full px-2.5 py-1 text-[0.65rem] font-semibold sm:block" style={{ color: CATEGORY_COLORS[index % CATEGORY_COLORS.length], backgroundColor: `${CATEGORY_COLORS[index % CATEGORY_COLORS.length]}18` }}>{document.category}</span><ArrowUpRight className="h-4 w-4 text-slate-300" /></Link>)}</div></section>;
}

function percent(value = 0, total = 0) { return total ? Math.round((value / total) * 100) : 0; }

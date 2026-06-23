import { AlertCircle, BarChart3, BrainCircuit, FileText, RefreshCw } from "lucide-react";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";

import { analyticsApi, getApiError } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

export default function Evaluation() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadEvaluation = useCallback(async () => {
    setRefreshing(true);
    try {
      const response = await analyticsApi.evaluation();
      setData(response.data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load evaluation metrics."));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadEvaluation();
  }, [loadEvaluation]);

  if (loading) {
    return <div className="panel grid min-h-[28rem] place-items-center rounded-lg"><LoadingSpinner label="Loading evaluation metrics" /></div>;
  }

  const classification = data?.classification || {};
  const summarization = data?.summarization || {};

  return (
    <>
      <PageHeader
        eyebrow="Evaluation"
        title="Model performance"
        description="Track classifier quality, confusion matrix results, and summarization quality signals."
        action={
          <button className="btn-secondary" onClick={loadEvaluation} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        }
      />

      <ErrorBanner message={error} />

      {!classification.available ? (
        <div className="panel rounded-lg p-5">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-none text-amber-400" />
            <p className="text-sm text-slate-600 dark:text-slate-300">{classification.message || "Classification metrics are not available."}</p>
          </div>
        </div>
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Accuracy" value={percent(classification.accuracy)} icon={BrainCircuit} />
            <MetricCard label="Precision" value={percent(classification.precision)} icon={BarChart3} />
            <MetricCard label="Recall" value={percent(classification.recall)} icon={BarChart3} />
            <MetricCard label="F1-score" value={percent(classification.f1_score)} icon={BarChart3} />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <ClassMetrics report={classification.classification_report || {}} labels={classification.labels || []} />
            <ConfusionMatrix matrix={classification.confusion_matrix || []} labels={classification.labels || []} />
          </section>
        </>
      )}

      <section className="mt-6 grid gap-4 sm:grid-cols-3">
        <MetricCard label="ROUGE-1" value={summarization.rouge_1 == null ? "N/A" : percent(summarization.rouge_1)} icon={FileText} />
        <MetricCard label="ROUGE-L" value={summarization.rouge_l == null ? "N/A" : percent(summarization.rouge_l)} icon={FileText} />
        <MetricCard label="Compression" value={summarization.compression_ratio == null ? "N/A" : percent(summarization.compression_ratio)} icon={FileText} />
      </section>

      <section className="panel mt-6 rounded-lg p-5">
        <h2 className="font-semibold text-slate-950 dark:text-white">Summarization evaluation</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
          {summarization.note || "Compression ratio is computed for generated summaries. ROUGE needs reference summaries."}
        </p>
        <p className="mt-3 text-xs font-semibold text-slate-400">
          {summarization.evaluated_documents || 0} summaries evaluated, {summarization.reference_summary_documents || 0} with reference summaries
        </p>
      </section>
    </>
  );
}

function MetricCard({ icon: Icon, label, value }) {
  return (
    <article className="panel rounded-lg p-5">
      <div className="flex items-center justify-between">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-vault-accent/10 text-vault-accent">
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-5 text-3xl font-extrabold text-slate-950 dark:text-white">{value}</p>
      <p className="mt-1 text-sm font-semibold text-slate-600 dark:text-slate-300">{label}</p>
    </article>
  );
}

function ClassMetrics({ report, labels }) {
  return (
    <section className="panel rounded-lg p-5">
      <h2 className="font-semibold text-slate-950 dark:text-white">Class metrics</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[32rem] text-left text-sm">
          <thead className="text-xs uppercase text-slate-400">
            <tr>
              <th className="py-2 pr-3">Class</th>
              <th className="py-2 pr-3">Precision</th>
              <th className="py-2 pr-3">Recall</th>
              <th className="py-2 pr-3">F1</th>
              <th className="py-2">Support</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200/70 dark:divide-white/[0.07]">
            {labels.map((label) => {
              const row = report[label] || {};
              return (
                <tr key={label}>
                  <td className="py-3 pr-3 font-semibold text-slate-800 dark:text-slate-100">{label}</td>
                  <td className="py-3 pr-3 text-slate-500 dark:text-slate-300">{percent(row.precision)}</td>
                  <td className="py-3 pr-3 text-slate-500 dark:text-slate-300">{percent(row.recall)}</td>
                  <td className="py-3 pr-3 text-slate-500 dark:text-slate-300">{percent(row["f1-score"])}</td>
                  <td className="py-3 text-slate-500 dark:text-slate-300">{row.support ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ConfusionMatrix({ matrix, labels }) {
  const max = useMemo(() => Math.max(...matrix.flat(), 1), [matrix]);
  return (
    <section className="panel rounded-lg p-5">
      <h2 className="font-semibold text-slate-950 dark:text-white">Confusion matrix</h2>
      <div className="mt-4 overflow-auto">
        <div className="grid min-w-[28rem] gap-1" style={{ gridTemplateColumns: `8rem repeat(${labels.length}, minmax(3rem, 1fr))` }}>
          <div />
          {labels.map((label) => <MatrixLabel key={label} label={label} />)}
          {matrix.map((row, rowIndex) => (
            <Fragment key={labels[rowIndex] || rowIndex}>
              <MatrixLabel key={`${labels[rowIndex]}-row`} label={labels[rowIndex]} align="right" />
              {row.map((value, columnIndex) => (
                <div
                  key={`${rowIndex}-${columnIndex}`}
                  className="grid min-h-12 place-items-center rounded-lg text-sm font-bold text-slate-900 dark:text-white"
                  style={{ backgroundColor: `rgba(20, 184, 166, ${0.08 + (value / max) * 0.42})` }}
                >
                  {value}
                </div>
              ))}
            </Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}

function MatrixLabel({ label, align = "center" }) {
  return (
    <div className={`truncate px-2 py-2 text-[0.68rem] font-semibold text-slate-400 ${align === "right" ? "text-right" : "text-center"}`}>
      {label}
    </div>
  );
}

function percent(value) {
  if (value == null || Number.isNaN(Number(value))) return "N/A";
  return `${Math.round(Number(value) * 100)}%`;
}

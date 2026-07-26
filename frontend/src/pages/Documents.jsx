import { FileText, Filter, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { documentsApi, getApiError } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All");
  useEffect(() => {
    documentsApi.list().then(({ data }) => setDocuments(data.documents || []))
      .catch((err) => setError(getApiError(err, "Unable to load the document register.")))
      .finally(() => setLoading(false));
  }, []);
  const filtered = useMemo(() => documents.filter((doc) => {
    const text = [doc.filename, doc.matter_name, doc.matter_number, doc.client_name, doc.predicted_category].join(" ").toLowerCase();
    return (status === "All" || doc.review_status === status) && text.includes(query.trim().toLowerCase());
  }), [documents, query, status]);
  return <>
    <PageHeader eyebrow="Records management" title="Document register" description="The authoritative register for client files, matters, review state, privilege, and retention." action={<Link className="btn-primary" to="/upload">Add document</Link>} />
    <ErrorBanner message={error} />
    <div className="panel mb-5 flex flex-col gap-3 rounded-2xl p-4 sm:flex-row">
      <label className="relative flex-1"><Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" /><input className="input pl-10" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search document, client, or matter reference" /></label>
      <label className="relative sm:w-52"><Filter className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" /><select className="input appearance-none pl-10" value={status} onChange={(e) => setStatus(e.target.value)}>{["All", "Needs review", "In review", "Approved", "Archived"].map((item) => <option key={item}>{item}</option>)}</select></label>
    </div>
    {loading ? <div className="panel rounded-2xl p-8"><LoadingSpinner label="Loading register" /></div> : filtered.length ? <section className="panel overflow-hidden rounded-2xl">
      <div className="hidden grid-cols-[2fr_1.2fr_1fr_0.8fr] gap-4 border-b border-slate-200/70 px-6 py-3 text-[0.65rem] font-bold uppercase tracking-wider text-slate-400 dark:border-white/[0.07] md:grid"><span>Document</span><span>Matter / client</span><span>Information controls</span><span>Status</span></div>
      <div className="divide-y divide-slate-200/70 dark:divide-white/[0.07]">{filtered.map((doc) => <DocumentRow key={doc.id} document={doc} />)}</div>
    </section> : <EmptyState title="No documents match" description="Adjust the search or status filter, or add a document to the register." />}
  </>;
}

function DocumentRow({ document: doc }) {
  const approved = doc.review_status === "Approved";
  return <Link to={`/documents/${doc.id}`} className="grid gap-3 px-5 py-4 transition hover:bg-slate-50/80 dark:hover:bg-white/[0.025] md:grid-cols-[2fr_1.2fr_1fr_0.8fr] md:items-center md:gap-4 md:px-6">
    <div className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-400/10 dark:text-teal-300"><FileText className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-sm font-bold text-slate-800 dark:text-white">{doc.filename}</span><span className="mt-0.5 block text-xs text-slate-400">{doc.document_type || doc.predicted_category} · {new Date(doc.upload_date).toLocaleDateString()}</span></span></div>
    <div className="min-w-0 text-xs"><p className="truncate font-semibold text-slate-700 dark:text-slate-200">{doc.matter_name || "Unassigned matter"}</p><p className="mt-1 truncate text-slate-400">{doc.matter_number || doc.client_name || "No reference"}</p></div>
    <div className="flex flex-wrap gap-1.5">{doc.privilege !== "Not privileged" && <span className="control-badge text-amber-700 dark:text-amber-300"><ShieldCheck className="h-3 w-3" /> Privileged</span>}<span className="control-badge">{doc.confidentiality}</span></div>
    <span className={`w-fit rounded-full px-2.5 py-1 text-[0.68rem] font-bold ${approved ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300" : "bg-amber-100 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300"}`}>{doc.review_status}</span>
  </Link>;
}

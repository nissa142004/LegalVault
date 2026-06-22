import { ExternalLink, FileText, Search, Sparkles, Trash2, UploadCloud } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { documentsApi, getApiError } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState("");
  const [openingId, setOpeningId] = useState("");
  const [error, setError] = useState("");

  async function loadDocuments() {
    try {
      const response = await documentsApi.list();
      setDocuments(response.data.documents || []);
    } catch (err) {
      setError(getApiError(err, "Unable to load documents."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleDelete(documentId) {
    const confirmed = window.confirm("Delete this uploaded document?");
    if (!confirmed) {
      return;
    }

    setDeletingId(documentId);
    setError("");

    try {
      await documentsApi.delete(documentId);
      setDocuments((currentDocuments) =>
        currentDocuments.filter((document) => document.id !== documentId),
      );
    } catch (err) {
      setError(getApiError(err, "Unable to delete document."));
    } finally {
      setDeletingId("");
    }
  }

  async function handleViewOriginalPdf(documentId) {
    setOpeningId(documentId);
    setError("");
    const pdfWindow = window.open("", "_blank");

    if (!pdfWindow) {
      setError("Unable to open the PDF. Allow pop-ups for this site and try again.");
      setOpeningId("");
      return;
    }

    pdfWindow.opener = null;

    try {
      const response = await documentsApi.getOriginal(documentId);
      const pdfBlob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/pdf",
      });
      const pdfUrl = URL.createObjectURL(pdfBlob);

      pdfWindow.location.href = pdfUrl;
      window.setTimeout(() => URL.revokeObjectURL(pdfUrl), 60_000);
    } catch (err) {
      pdfWindow.close();
      setError(getApiError(err, "Unable to open the original PDF."));
    } finally {
      setOpeningId("");
    }
  }

  const processedCount = useMemo(
    () => documents.filter((document) => document.has_nlp_results).length,
    [documents],
  );

  return (
    <>
      <PageHeader
        eyebrow="Workspace"
        title="Dashboard"
        description="Track uploaded legal files, extracted text, and documents ready for intelligent search."
        action={
          <Link className="btn-primary" to="/upload">
            <UploadCloud className="h-4 w-4" />
            Upload
          </Link>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Metric icon={FileText} label="Documents" value={documents.length} />
        <Metric icon={Sparkles} label="Processed" value={processedCount} />
        <Metric icon={Search} label="Searchable" value={documents.filter((doc) => doc.has_raw_text).length} />
      </div>

      <section className="mt-6">
        <ErrorBanner message={error} />
        {loading ? (
          <div className="panel rounded-lg p-6">
            <LoadingSpinner label="Loading documents" />
          </div>
        ) : documents.length === 0 ? (
          <EmptyState
            title="No documents yet"
            description="Upload a PDF or DOCX file to extract text, summarize it, and make it searchable."
            action={
              <Link className="btn-primary" to="/upload">
                <UploadCloud className="h-4 w-4" />
                Upload document
              </Link>
            }
          />
        ) : (
          <div className="panel overflow-hidden rounded-lg">
            <div className="divide-y divide-slate-200 dark:divide-white/10">
              {documents.map((document) => (
                <div
                  key={document.id}
                  className="grid gap-3 p-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.04] sm:grid-cols-[1fr_auto]"
                >
                  <Link to={`/documents/${document.id}`} className="min-w-0">
                    <h2 className="truncate font-semibold text-slate-950 dark:text-white">{document.filename}</h2>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      Uploaded {new Date(document.upload_date).toLocaleString()}
                    </p>
                  </Link>
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <Status active={document.has_raw_text} label="Text" />
                    <Status active={document.has_nlp_results} label="NLP" />
                    {document.filename?.toLowerCase().endsWith(".pdf") ? (
                      <button
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:border-vault-accent/40 hover:text-vault-accent disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
                        type="button"
                        onClick={() => handleViewOriginalPdf(document.id)}
                        disabled={openingId === document.id}
                        title="View original PDF"
                      >
                        {openingId === document.id ? (
                          <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
                        ) : (
                          <ExternalLink className="h-4 w-4" />
                        )}
                      </button>
                    ) : null}
                    <button
                      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-red-400/20 bg-red-500/10 text-red-200 transition hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                      type="button"
                      onClick={() => handleDelete(document.id)}
                      disabled={deletingId === document.id}
                      title="Delete document"
                    >
                      {deletingId === document.id ? (
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-red-200 border-t-transparent" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="panel rounded-lg p-5">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-vault-accent dark:bg-white/[0.06]">
        <Icon className="h-5 w-5" />
      </div>
      <p className="text-3xl font-bold text-slate-950 dark:text-white">{value}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{label}</p>
    </div>
  );
}

function Status({ active, label }) {
  return (
    <span
      className={[
        "rounded-full px-3 py-1 font-medium",
        active
          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-200"
          : "bg-slate-100 text-slate-500 dark:bg-white/[0.06] dark:text-slate-400",
      ].join(" ")}
    >
      {label}
    </span>
  );
}

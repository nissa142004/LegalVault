import { ArrowLeft, ExternalLink, FileText, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { documentsApi, getApiError } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

export default function DocumentDetails() {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [openingOriginal, setOpeningOriginal] = useState(false);

  async function loadDocument() {
    setError("");
    try {
      const response = await documentsApi.getText(documentId);
      setDocument(response.data.document);
    } catch (err) {
      setError(getApiError(err, "Unable to load document."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocument();
  }, [documentId]);

  async function handleProcess() {
    setProcessing(true);
    setError("");

    try {
      await documentsApi.process(documentId);
      await loadDocument();
    } catch (err) {
      setError(getApiError(err, "Unable to process document."));
    } finally {
      setProcessing(false);
    }
  }

  async function handleViewOriginalPdf() {
    setOpeningOriginal(true);
    setError("");
    const pdfWindow = window.open("", "_blank");

    if (!pdfWindow) {
      setError("Unable to open the PDF. Allow pop-ups for this site and try again.");
      setOpeningOriginal(false);
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
      setOpeningOriginal(false);
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm("Delete this uploaded document?");
    if (!confirmed) {
      return;
    }

    setDeleting(true);
    setError("");

    try {
      await documentsApi.delete(documentId);
      navigate("/dashboard");
    } catch (err) {
      setError(getApiError(err, "Unable to delete document."));
    } finally {
      setDeleting(false);
    }
  }

  const isPdf = document?.filename?.toLowerCase().endsWith(".pdf");
  const topKeywords = document?.keywords?.slice(0, 10) || [];

  return (
    <>
      <PageHeader
        eyebrow="Document"
        title={document?.filename || "Document details"}
        description="Review the document summary and its most important legal keywords."
        action={
          <div className="flex gap-2">
            <Link className="btn-secondary" to="/dashboard">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            {document ? (
              <button
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-100 transition hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-red-100 border-t-transparent" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete
              </button>
            ) : null}
          </div>
        }
      />

      <ErrorBanner message={error} />

      {loading ? (
        <div className="panel rounded-lg p-6">
          <LoadingSpinner label="Loading document" />
        </div>
      ) : document ? (
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="space-y-6">
            <div className="panel rounded-lg p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-vault-accent dark:bg-white/[0.06]">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-semibold text-slate-950 dark:text-white">{document.filename}</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Uploaded {new Date(document.upload_date).toLocaleString()}
                  </p>
                </div>
              </div>

              <button className="btn-primary mt-5 w-full" onClick={handleProcess} disabled={processing}>
                {processing ? <LoadingSpinner label="Processing" /> : <Sparkles className="h-4 w-4" />}
                {!processing ? "Generate summary and legal keywords" : null}
              </button>
              {isPdf ? (
                <button
                  className="btn-secondary mt-3 w-full"
                  onClick={handleViewOriginalPdf}
                  disabled={openingOriginal}
                  type="button"
                >
                  {openingOriginal ? <LoadingSpinner label="Opening" /> : <ExternalLink className="h-4 w-4" />}
                  {!openingOriginal ? "View original PDF" : null}
                </button>
              ) : null}
            </div>

            <InfoPanel title="Summary" empty="No summary generated yet.">
              {document.summary}
            </InfoPanel>

            <div className="panel rounded-lg p-5">
              <h2 className="font-semibold text-slate-950 dark:text-white">Important legal keywords</h2>
              {topKeywords.length ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {topKeywords.map((keyword) => (
                    <span key={keyword} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-white/[0.06] dark:text-slate-300">
                      {keyword}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">No important legal keywords extracted yet.</p>
              )}
            </div>
          </section>

          <section className="panel rounded-lg p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="font-semibold text-slate-950 dark:text-white">Extracted text</h2>
              <RefreshCw className="h-4 w-4 text-slate-400 dark:text-slate-500" />
            </div>
            <div className="max-h-[34rem] overflow-auto rounded-lg border border-slate-200 bg-slate-50/90 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-vault-950/60 dark:text-slate-300">
              {document.raw_text || document.cleaned_text || "No extracted text available."}
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}

function InfoPanel({ title, empty, children }) {
  return (
    <div className="panel rounded-lg p-5">
      <h2 className="font-semibold text-slate-950 dark:text-white">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{children || empty}</p>
    </div>
  );
}

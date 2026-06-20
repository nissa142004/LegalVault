import { CheckCircle2, FileUp } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { documentsApi, getApiError } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

export default function Upload() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploadedDocument, setUploadedDocument] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF or DOCX document first.");
      return;
    }

    setError("");
    setLoading(true);
    setUploadedDocument(null);

    try {
      const response = await documentsApi.upload(file);
      setUploadedDocument(response.data.document);
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (err) {
      setError(getApiError(err, "Unable to upload document."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Ingest"
        title="Upload document"
        description="Upload legal PDFs and DOCX files for text extraction, summarization, keyword detection, and search."
      />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <form onSubmit={handleUpload} className="panel rounded-lg p-5 sm:p-6">
          <ErrorBanner message={error} />
          <label className="mt-4 block rounded-lg border border-dashed border-slate-300 bg-slate-50/80 p-8 text-center transition hover:border-vault-accent/60 dark:border-white/15 dark:bg-vault-950/50">
            <FileUp className="mx-auto h-10 w-10 text-vault-accent" />
            <span className="mt-4 block text-sm font-semibold text-slate-950 dark:text-white">
              {file ? file.name : "Choose a legal document"}
            </span>
            <span className="mt-2 block text-xs text-slate-500 dark:text-slate-400">PDF and DOCX files are supported</span>
            <input
              ref={inputRef}
              className="sr-only"
              type="file"
              accept=".pdf,.docx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>

          <button className="btn-primary mt-5 w-full" type="submit" disabled={loading}>
            {loading ? <LoadingSpinner label="Uploading" /> : <FileUp className="h-4 w-4" />}
            {!loading ? "Upload and extract text" : null}
          </button>
        </form>

        <aside className="panel rounded-lg p-5 sm:p-6">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Processing pipeline</h2>
          <div className="mt-5 space-y-4 text-sm text-slate-600 dark:text-slate-300">
            <Step label="Secure upload" />
            <Step label="Text extraction" />
            <Step label="Clean legal text" />
            <Step label="Ready for search" />
          </div>

          {uploadedDocument ? (
            <div className="mt-6 rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-4">
              <div className="flex gap-3">
                <CheckCircle2 className="h-5 w-5 flex-none text-emerald-300" />
                <div>
                  <p className="font-semibold text-emerald-100">{uploadedDocument.filename}</p>
                  <p className="mt-1 text-sm text-emerald-100/75">Document text extracted successfully.</p>
                  <Link className="btn-secondary mt-4" to={`/documents/${uploadedDocument.id}`}>
                    View details
                  </Link>
                </div>
              </div>
            </div>
          ) : null}
        </aside>
      </div>
    </>
  );
}

function Step({ label }) {
  return (
    <div className="flex items-center gap-3">
      <span className="h-2.5 w-2.5 rounded-full bg-vault-accent" />
      <span>{label}</span>
    </div>
  );
}

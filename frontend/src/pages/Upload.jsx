import { AlertTriangle, CheckCircle2, FileText, FileUp, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { documentsApi, getApiError } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

const SUPPORTED_EXTENSIONS = [".pdf", ".docx"];

export default function Upload() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploadedDocument, setUploadedDocument] = useState(null);
  const [uploadInsight, setUploadInsight] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [metadata, setMetadata] = useState({
    client_name: "", matter_name: "", matter_number: "", document_type: "",
    document_date: "", retention_date: "", confidentiality: "Confidential",
    privilege: "Not privileged",
  });

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF or DOCX document first.");
      return;
    }

    setError("");
    setLoading(true);
    setUploadedDocument(null);
    setUploadInsight(null);

    try {
      const response = await documentsApi.upload(file, metadata);
      setUploadedDocument(response.data.document);
      setUploadInsight({
        classification: response.data.classification,
        similarDocuments: response.data.similar_documents || [],
      });
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

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0] || null;
    const extension = selectedFile ? selectedFile.name.slice(selectedFile.name.lastIndexOf(".")).toLowerCase() : "";

    if (selectedFile && !SUPPORTED_EXTENSIONS.includes(extension)) {
      setFile(null);
      setError("Only PDF and DOCX files are supported.");
      event.target.value = "";
      return;
    }

    setError("");
    setFile(selectedFile);
  }

  return (
    <>
      <PageHeader
        eyebrow="Ingest"
        title="Upload document"
        description="Upload legal PDFs and DOCX files for text extraction, keyword detection, classification, and search."
      />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <form onSubmit={handleUpload} className="panel rounded-lg p-5 sm:p-6">
          <ErrorBanner message={error} />
          <div className="mb-5 grid gap-4 sm:grid-cols-2">
            <Field label="Client name" name="client_name" value={metadata.client_name} onChange={setMetadata} placeholder="Northstar Holdings" />
            <Field label="Matter reference" name="matter_number" value={metadata.matter_number} onChange={setMetadata} placeholder="LIT-2026-0142" />
            <Field label="Matter name" name="matter_name" value={metadata.matter_name} onChange={setMetadata} placeholder="Commercial dispute" />
            <Field label="Document type" name="document_type" value={metadata.document_type} onChange={setMetadata} placeholder="Witness statement" />
            <Field label="Document date" name="document_date" type="date" value={metadata.document_date} onChange={setMetadata} />
            <Field label="Retention review" name="retention_date" type="date" value={metadata.retention_date} onChange={setMetadata} />
            <SelectField label="Confidentiality" name="confidentiality" value={metadata.confidentiality} onChange={setMetadata} options={["Public", "Internal", "Confidential", "Highly confidential"]} />
            <SelectField label="Legal privilege" name="privilege" value={metadata.privilege} onChange={setMetadata} options={["Not privileged", "Attorney-client privileged", "Attorney work product"]} />
          </div>
          <label className="block rounded-lg border border-dashed border-slate-300 bg-slate-50/80 p-8 text-center transition hover:border-vault-accent/60 dark:border-white/15 dark:bg-vault-950/50">
            <FileUp className="mx-auto h-10 w-10 text-vault-accent" />
            <span className="mt-4 block text-sm font-semibold text-slate-950 dark:text-white">
              {file ? file.name : "Choose a legal document"}
            </span>
            <span className="mt-2 block text-xs text-slate-500 dark:text-slate-400">PDF and DOCX files are supported</span>
            <input
              ref={inputRef}
              className="sr-only"
              type="file"
              onChange={handleFileChange}
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
            <Step label="AI classification" />
            <Step label="Legal keyword extraction" />
            <Step label="Similar document matching" />
          </div>

          {uploadedDocument ? (
            <div className="mt-6 rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-4">
              <div className="flex gap-3">
                <CheckCircle2 className="h-5 w-5 flex-none text-emerald-600 dark:text-emerald-300" />
                <div>
                  <p className="font-semibold text-emerald-800 dark:text-emerald-100">{uploadedDocument.filename}</p>
                  <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-100/75">Document intelligence generated successfully.</p>
                  <Link className="btn-secondary mt-4" to={`/documents/${uploadedDocument.id}`}>
                    View details
                  </Link>
                </div>
              </div>
            </div>
          ) : null}

          {uploadInsight?.classification ? (
            <div className="mt-4 rounded-lg border border-slate-200/80 bg-white/70 p-4 dark:border-white/10 dark:bg-white/[0.04]">
              <div className="flex items-start gap-3">
                {uploadInsight.classification.warning ? (
                  <AlertTriangle className="mt-0.5 h-5 w-5 flex-none text-amber-400" />
                ) : (
                  <Sparkles className="mt-0.5 h-5 w-5 flex-none text-vault-accent" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-950 dark:text-white">
                    {uploadInsight.classification.predicted_category}
                    {uploadInsight.classification.confidence_percentage != null ? (
                      <span className="ml-2 text-xs text-slate-400">
                        {uploadInsight.classification.confidence_percentage}%
                      </span>
                    ) : null}
                  </p>
                  {uploadInsight.classification.warning ? (
                    <p className="mt-1 text-xs leading-5 text-amber-600 dark:text-amber-300">
                      {uploadInsight.classification.warning}
                    </p>
                  ) : null}
                  <div className="mt-3 space-y-2">
                    {(uploadInsight.classification.top_predictions || []).map((item) => (
                      <PredictionBar key={item.category} item={item} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {uploadInsight?.similarDocuments?.length ? (
            <div className="mt-4 rounded-lg border border-slate-200/80 bg-white/70 p-4 dark:border-white/10 dark:bg-white/[0.04]">
              <h3 className="text-sm font-semibold text-slate-950 dark:text-white">Similar documents</h3>
              <div className="mt-3 space-y-2">
                {uploadInsight.similarDocuments.map((item) => (
                  <Link
                    key={item.document_id}
                    to={`/documents/${item.document_id}`}
                    className="flex items-center justify-between gap-3 rounded-lg px-2 py-2 text-sm transition hover:bg-slate-100 dark:hover:bg-white/[0.05]"
                  >
                    <span className="flex min-w-0 items-center gap-2 text-slate-700 dark:text-slate-200">
                      <FileText className="h-4 w-4 flex-none text-slate-400" />
                      <span className="truncate">{item.document_name}</span>
                    </span>
                    <span className="flex-none text-xs font-bold text-vault-accent">
                      {item.similarity_percentage}%
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          ) : null}
        </aside>
      </div>
    </>
  );
}

function PredictionBar({ item }) {
  const width = `${Math.max(4, Math.min(item.percentage || 0, 100))}%`;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-xs">
        <span className="truncate font-semibold text-slate-600 dark:text-slate-300">{item.category}</span>
        <span className="flex-none text-slate-400">{item.percentage}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-white/[0.07]">
        <div className="h-full rounded-full bg-vault-accent" style={{ width }} />
      </div>
    </div>
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

function Field({ label, name, onChange, ...props }) {
  return <label><span className="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-300">{label}</span><input className="input" name={name} onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))} {...props} /></label>;
}

function SelectField({ label, name, value, onChange, options }) {
  return <label><span className="mb-1.5 block text-xs font-bold text-slate-600 dark:text-slate-300">{label}</span><select className="input" value={value} onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))}>{options.map((option) => <option key={option}>{option}</option>)}</select></label>;
}

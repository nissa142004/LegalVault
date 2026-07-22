import { AlertTriangle, FileSearch, Filter, Search as SearchIcon, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { documentsApi, getApiError } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import PageHeader from "../components/PageHeader";

export default function Search() {
  const [query, setQuery] = useState("");
  const [searched, setSearched] = useState(false);
  const [results, setResults] = useState([]);
  const [searchMeta, setSearchMeta] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSearch(event) {
    event.preventDefault();
    if (!query.trim()) {
      setError("Enter a search query.");
      return;
    }

    setError("");
    setLoading(true);
    setSearched(true);
    setSearchMeta(null);

    try {
      const response = await documentsApi.search(query.trim());
      setResults(response.data.results || []);
      setSearchMeta({
        queryClassification: response.data.query_classification,
        categoryFilter: response.data.category_filter,
      });
    } catch (err) {
      setError(getApiError(err, "Unable to search documents."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Retrieval"
        title="Intelligent search"
        description="Search cleaned legal documents with TF-IDF vectors and cosine similarity ranking."
      />

      <form onSubmit={handleSearch} className="panel rounded-lg p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="input"
            placeholder="Search for clauses, issues, parties, obligations..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="btn-primary sm:w-40" type="submit" disabled={loading}>
            {loading ? <LoadingSpinner label="Searching" /> : <SearchIcon className="h-4 w-4" />}
            {!loading ? "Search" : null}
          </button>
        </div>
      </form>

      <div className="mt-5">
        <ErrorBanner message={error} />
      </div>

      {searched && !loading && searchMeta?.queryClassification ? (
        <section className="panel mt-5 rounded-lg p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              {searchMeta.queryClassification.warning ? (
                <AlertTriangle className="mt-0.5 h-5 w-5 flex-none text-amber-400" />
              ) : (
                <Sparkles className="mt-0.5 h-5 w-5 flex-none text-vault-accent" />
              )}
              <div>
                <p className="text-sm font-semibold text-slate-950 dark:text-white">
                  Query classified as {searchMeta.queryClassification.predicted_category}
                </p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Confidence {searchMeta.queryClassification.confidence_percentage}%
                </p>
              </div>
            </div>
            <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300">
              <Filter className="h-3.5 w-3.5" />
              {searchMeta.categoryFilter ? `Filtered to ${searchMeta.categoryFilter}` : "Searching all categories"}
            </div>
          </div>
          {searchMeta.queryClassification.warning ? (
            <p className="mt-3 text-xs leading-5 text-amber-600 dark:text-amber-300">
              {searchMeta.queryClassification.warning}
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="mt-5 space-y-4">
        {loading ? (
          <div className="panel rounded-lg p-6">
            <LoadingSpinner label="Ranking documents" />
          </div>
        ) : searched && results.length === 0 ? (
          <EmptyState
            title="No relevant matches"
            description="Try a different legal term, phrase, party name, or clause topic."
          />
        ) : results.length > 0 ? (
          results.map((result) => <SearchResult key={result.document_id} result={result} />)
        ) : (
          <div className="panel rounded-lg p-8 text-center">
            <FileSearch className="mx-auto h-10 w-10 text-vault-accent" />
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">Run a query to rank your legal archive.</p>
          </div>
        )}
      </section>
    </>
  );
}

function SearchResult({ result }) {
  return (
    <article className="panel rounded-lg p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link
            to={`/documents/${result.document_id}`}
            className="text-lg font-semibold text-slate-950 hover:text-vault-accent dark:text-white"
          >
            {result.title}
          </Link>
          <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{result.summary}</p>
        </div>
        <div className="flex flex-none flex-col items-start gap-2 sm:items-end">
          <div className="rounded-lg border border-teal-300 bg-teal-50 px-3 py-2 text-sm font-bold text-teal-800 dark:border-vault-accent/20 dark:bg-vault-accent/10 dark:text-vault-accent">
            {result.similarity_percentage ?? Math.round(result.similarity_score * 100)}%
          </div>
          {result.predicted_category ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[0.65rem] font-semibold text-slate-500 dark:bg-white/[0.06] dark:text-slate-300">
              {result.predicted_category}
            </span>
          ) : null}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {(result.keywords || []).slice(0, 5).map((keyword) => (
          <span key={keyword} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-white/[0.06] dark:text-slate-300">
            {keyword}
          </span>
        ))}
      </div>
    </article>
  );
}

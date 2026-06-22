import { FileSearch, Search as SearchIcon } from "lucide-react";
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

    try {
      const response = await documentsApi.search(query.trim());
      setResults(response.data.results || []);
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
        <div className="rounded-lg border border-vault-accent/20 bg-vault-accent/10 px-3 py-2 text-sm font-bold text-vault-accent">
          {Math.round(result.similarity_score * 100)}%
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

export default function LoadingSpinner({ label = "Loading" }) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-vault-accent border-t-transparent" />
      <span>{label}</span>
    </div>
  );
}

import { FileText } from "lucide-react";

export default function EmptyState({ title, description, action }) {
  return (
    <div className="panel flex min-h-64 flex-col items-center justify-center rounded-lg p-8 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-vault-accent dark:bg-white/[0.06]">
        <FileText className="h-6 w-6" />
      </div>
      <h2 className="text-lg font-semibold text-slate-950 dark:text-white">{title}</h2>
      <p className="mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

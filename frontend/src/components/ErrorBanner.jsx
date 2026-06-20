import { AlertTriangle } from "lucide-react";

export default function ErrorBanner({ message }) {
  if (!message) {
    return null;
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-300/60 bg-red-50 p-4 text-sm text-red-700 dark:border-red-400/25 dark:bg-red-500/10 dark:text-red-100">
      <AlertTriangle className="mt-0.5 h-4 w-4 flex-none text-red-500 dark:text-red-300" />
      <p>{message}</p>
    </div>
  );
}

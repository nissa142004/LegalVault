import { CheckCircle2 } from "lucide-react";

export default function SuccessBanner({ message }) {
  if (!message) {
    return null;
  }

  return (
    <div className="mb-6 flex items-start gap-3 rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm text-teal-800 dark:border-teal-400/20 dark:bg-teal-400/10 dark:text-teal-200">
      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none text-teal-600 dark:text-teal-300" />
      <p>{message}</p>
    </div>
  );
}
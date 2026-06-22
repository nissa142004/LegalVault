export default function ProductLogo({ className = "h-11 w-11", decorative = false }) {
  return (
    <img
      src="/legalvault-logo.png"
      alt={decorative ? "" : "LegalVault shield logo"}
      aria-hidden={decorative || undefined}
      className={`object-contain drop-shadow-[0_6px_14px_rgba(3,28,61,0.22)] ${className}`}
    />
  );
}

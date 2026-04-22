type CatalystMarkProps = {
  className?: string;
};

export default function CatalystMark({ className = "" }: CatalystMarkProps) {
  return (
    <div
      className={`flex h-10 w-10 items-center justify-center rounded-lg bg-[#155EEF] text-white shadow-[0_0_24px_rgba(21,94,239,0.28)] ${className}`}
      aria-hidden="true"
    >
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
        <rect x="4" y="2" width="5" height="20" rx="2.5" fill="currentColor" />
        <rect x="11" y="4" width="9" height="4.5" rx="2.25" fill="currentColor" />
        <rect x="11" y="10" width="5" height="4.5" rx="2.25" fill="currentColor" opacity="0.62" />
        <rect x="11" y="16" width="9" height="4.5" rx="2.25" fill="currentColor" />
      </svg>
    </div>
  );
}

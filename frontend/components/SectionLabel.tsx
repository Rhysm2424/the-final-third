export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <span className="h-px w-8 bg-navy" />
      <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.15em] text-navy">
        {children}
      </span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}

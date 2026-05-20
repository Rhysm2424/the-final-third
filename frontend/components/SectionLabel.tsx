export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="label-mono mb-3.5 flex items-center gap-3">
      <span>{children}</span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}

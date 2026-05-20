'use client';

export function DemoBanner() {
  const isDemo = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
  if (!isDemo) return null;

  return (
    <div
      className="w-full bg-signal-gold/90 text-ink"
      role="alert"
      aria-label="Demo mode banner"
    >
      <div className="container-narrow flex items-center justify-between gap-3 py-2 text-xs">
        <span className="font-mono uppercase tracking-wider">Demo Mode</span>
        <span className="font-sans text-[11px] sm:text-xs">
          Data shown is illustrative seed data. Set <code className="font-mono">DEMO_MODE=false</code> on the backend to switch to live ingestion.
        </span>
      </div>
    </div>
  );
}

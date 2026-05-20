'use client';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-start gap-4 py-16">
      <div className="label-mono text-signal-red">Something broke</div>
      <h2 className="display-serif text-2xl">We couldn&rsquo;t load this page.</h2>
      <p className="max-w-prose text-ink/65">
        The API may be unavailable. If you&rsquo;re running locally, check that the backend
        container is up.
      </p>
      <pre className="font-mono text-xs text-ink/50">{error.message}</pre>
      <button
        onClick={reset}
        className="rounded bg-navy px-4 py-2 font-mono text-xs uppercase tracking-wider text-cream"
      >
        Try again
      </button>
    </div>
  );
}

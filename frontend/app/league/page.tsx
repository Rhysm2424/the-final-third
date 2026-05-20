import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { formatProb } from '@/lib/utils';

export const revalidate = 0;

export default async function LeaguePage() {
  let data;
  try {
    data = await api.league('PL');
  } catch {
    data = null;
  }

  return (
    <div>
      <PageHeader
        kicker="Projections"
        title="Where every team finishes."
        dek="Final-position projections from 10,000 simulated rest-of-season runs. Updated after every matchday."
      />

      {!data || data.rows.length === 0 ? (
        <div className="surface p-8 text-center text-sm text-ink/55">
          No projections available yet.
        </div>
      ) : (
        <div className="surface overflow-hidden">
          <div className="label-mono grid grid-cols-[36px_1fr_60px_80px_80px_80px_80px] gap-3 border-b border-line bg-cream-50 px-5 py-3">
            <span>#</span>
            <span>Team</span>
            <span className="text-right">xPts</span>
            <span className="text-right">Title</span>
            <span className="text-right">Top 4</span>
            <span className="text-right">Rel.</span>
            <span className="text-right">xPos</span>
          </div>
          {data.rows.map((row, idx) => (
            <div
              key={row.team.id}
              className="grid grid-cols-[36px_1fr_60px_80px_80px_80px_80px] items-center gap-3 border-b border-line px-5 py-3 last:border-b-0 hover:bg-cream-50"
            >
              <span className="font-mono text-sm text-ink/50">{idx + 1}</span>
              <span className="font-serif text-base font-semibold">{row.team.short_name}</span>
              <span className="text-right font-mono text-sm tabular-nums">
                {row.expected_points.toFixed(1)}
              </span>
              <span className="text-right font-mono text-sm tabular-nums">
                {row.title_probability >= 0.005 ? formatProb(row.title_probability) : '—'}
              </span>
              <span className="text-right font-mono text-sm tabular-nums">
                {formatProb(row.top_four_probability)}
              </span>
              <span className="text-right font-mono text-sm tabular-nums">
                {formatProb(row.relegation_probability)}
              </span>
              <span className="text-right font-mono text-sm tabular-nums text-ink/55">
                {row.expected_position.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { cn, formatProb } from '@/lib/utils';

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
        <div className="overflow-hidden rounded-md border border-line bg-paper">
          <div className="grid grid-cols-[6px_36px_1fr_72px_72px_72px_72px_72px] gap-x-3 border-b border-line bg-navy px-4 py-3 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-cream/65">
            <span />
            <span>#</span>
            <span>Team</span>
            <span className="text-right">xPts</span>
            <span className="text-right">Title</span>
            <span className="text-right">Top 4</span>
            <span className="text-right">Rel.</span>
            <span className="text-right">xPos</span>
          </div>
          {data.rows.map((row, idx) => {
            const position = idx + 1;
            const indicator =
              row.title_probability >= 0.05
                ? 'bg-signal-gold'
                : row.top_four_probability >= 0.5
                  ? 'bg-navy'
                  : row.relegation_probability >= 0.5
                    ? 'bg-signal-red'
                    : row.relegation_probability >= 0.15
                      ? 'bg-signal-red/40'
                      : 'bg-transparent';
            return (
              <div
                key={row.team.id}
                className="group grid grid-cols-[6px_36px_1fr_72px_72px_72px_72px_72px] items-center gap-x-3 border-b border-line px-4 py-3 last:border-b-0 hover:bg-cream-50"
              >
                <span className={cn('h-7 w-1 rounded-sm transition-all group-hover:h-9', indicator)} />
                <span className="font-mono text-sm text-ink/45 tabular-nums">{position}</span>
                <span className="font-serif text-base font-semibold">
                  {row.team.short_name}
                </span>
                <span className="text-right font-mono text-sm tabular-nums">
                  {row.expected_points.toFixed(1)}
                </span>
                <span
                  className={cn(
                    'text-right font-mono text-sm tabular-nums',
                    row.title_probability >= 0.05 ? 'font-semibold text-ink' : 'text-ink/50'
                  )}
                >
                  {row.title_probability >= 0.005 ? formatProb(row.title_probability) : '—'}
                </span>
                <span
                  className={cn(
                    'text-right font-mono text-sm tabular-nums',
                    row.top_four_probability >= 0.5
                      ? 'font-semibold text-navy'
                      : 'text-ink/60'
                  )}
                >
                  {formatProb(row.top_four_probability)}
                </span>
                <span
                  className={cn(
                    'text-right font-mono text-sm tabular-nums',
                    row.relegation_probability >= 0.5
                      ? 'font-semibold text-signal-red'
                      : row.relegation_probability >= 0.15
                        ? 'text-signal-red/80'
                        : 'text-ink/40'
                  )}
                >
                  {formatProb(row.relegation_probability)}
                </span>
                <span className="text-right font-mono text-sm tabular-nums text-ink/50">
                  {row.expected_position.toFixed(1)}
                </span>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-ink/60">
        <LegendDot color="bg-signal-gold" label="Title contender" />
        <LegendDot color="bg-navy" label="Top 4 likely" />
        <LegendDot color="bg-signal-red/40" label="Relegation threat" />
        <LegendDot color="bg-signal-red" label="Relegation likely" />
      </div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn('h-2.5 w-2.5 rounded-sm', color)} />
      <span className="font-mono text-[10px] uppercase tracking-[0.1em]">{label}</span>
    </span>
  );
}

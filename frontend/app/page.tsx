import { api } from '@/lib/api';
import type { MatchSummary } from '@/lib/types';
import { PageHeader } from '@/components/PageHeader';
import { FixtureRow } from '@/components/FixtureRow';

export const revalidate = 0;

export default async function FixturesPage() {
  let fixtures: MatchSummary[] = [];
  try {
    fixtures = await api.fixtures({ days_ahead: 21, days_back: 7 });
  } catch {
    // The error boundary handles render failure, but for an empty API we
    // degrade gracefully.
  }

  const grouped = groupByDay(fixtures);

  return (
    <div>
      <PageHeader
        kicker="This Weekend"
        title="The matches, modelled."
        dek="Probabilistic forecasts grounded in historical match data, calibrated against closing market prices. Every number on this site is a claim we keep score of."
      />

      {fixtures.length === 0 && (
        <div className="surface p-8 text-center text-sm text-ink/55">
          No fixtures in the current window. If you&rsquo;re in live mode, run{' '}
          <code className="font-mono">make ingest</code> to populate.
        </div>
      )}

      {Object.entries(grouped).map(([dayLabel, matches]) => (
        <section key={dayLabel} className="mb-6">
          <div className="label-mono border-b border-line pb-2.5 pt-5">{dayLabel}</div>
          {matches.map((m, i) => (
            <FixtureRow key={m.id} match={m} index={i} />
          ))}
        </section>
      ))}
    </div>
  );
}

function groupByDay(fixtures: MatchSummary[]): Record<string, MatchSummary[]> {
  return fixtures.reduce(
    (acc, m) => {
      const d = new Date(m.kickoff);
      const label =
        d.toLocaleDateString('en-GB', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          timeZone: 'UTC',
        }) +
        ` — ${m.competition.name}`;
      if (!acc[label]) acc[label] = [];
      acc[label].push(m);
      return acc;
    },
    {} as Record<string, MatchSummary[]>
  );
}

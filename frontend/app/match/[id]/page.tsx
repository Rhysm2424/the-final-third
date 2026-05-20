import Link from 'next/link';
import { notFound } from 'next/navigation';
import { api } from '@/lib/api';
import { ProbabilityBar } from '@/components/ProbabilityBar';
import { StatRow } from '@/components/StatRow';
import { SectionLabel } from '@/components/SectionLabel';
import { DriverList } from '@/components/DriverList';
import { NarrativeBlock } from '@/components/NarrativeBlock';
import { ScorelineGrid } from '@/components/ScorelineGrid';
import { formatKickoff, formatProb, formatXg } from '@/lib/utils';

export const revalidate = 0;

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function MatchPage({ params }: PageProps) {
  const { id } = await params;
  const matchId = Number(id);
  if (Number.isNaN(matchId)) notFound();

  let match;
  try {
    match = await api.match(matchId);
  } catch {
    notFound();
  }
  if (!match) notFound();

  const kickoff = formatKickoff(match.kickoff);
  const pred = match.prediction;
  const marketImplied = computeMarketImplied(
    match.odds_home,
    match.odds_draw,
    match.odds_away
  );

  return (
    <div>
      <Link
        href="/"
        className="label-mono mb-6 inline-block transition-colors hover:text-navy"
      >
        ← All fixtures
      </Link>

      <div className="mb-8 border-b border-line pb-7">
        <div className="label-mono mb-3 text-navy">
          {match.competition.name} ·{' '}
          {kickoff.full}
          {match.venue && ` · ${match.venue}`}
        </div>
        <h1 className="display-serif text-4xl leading-none sm:text-5xl">
          {match.home_team.short_name}
          <span className="mx-3 align-middle text-3xl italic text-ink/40 sm:text-4xl">
            v
          </span>
          {match.away_team.short_name}
        </h1>
        {match.matchday && (
          <div className="mt-3 font-serif text-base italic text-ink/55">
            Matchday {match.matchday}
          </div>
        )}
      </div>

      {pred ? (
        <>
          <div className="mb-8">
            <SectionLabel>Match Outcome</SectionLabel>
            <ProbabilityBar
              homeLabel={match.home_team.short_name}
              awayLabel={match.away_team.short_name}
              probHome={pred.prob_home}
              probDraw={pred.prob_draw}
              probAway={pred.prob_away}
              marketImplied={marketImplied}
            />
          </div>

          <div className="mb-8">
            <SectionLabel>Expected Goals</SectionLabel>
            <StatRow
              cells={[
                {
                  label: 'Expected Goals',
                  value: `${formatXg(pred.home_xg)} — ${formatXg(pred.away_xg)}`,
                },
                pred.scoreline_distribution && pred.scoreline_distribution[0]
                  ? {
                      label: 'Most Likely Score',
                      value: `${pred.scoreline_distribution[0].home}–${pred.scoreline_distribution[0].away}`,
                      sub: formatProb(pred.scoreline_distribution[0].prob),
                    }
                  : { label: 'Most Likely Score', value: '—' },
                {
                  label: 'Over 2.5 Goals',
                  value: formatProb(pred.prob_over_2_5),
                },
              ]}
            />
          </div>

          {pred.narrative && (
            <div className="mb-8">
              <SectionLabel>The Story</SectionLabel>
              <NarrativeBlock text={pred.narrative} />
            </div>
          )}

          {pred.drivers && pred.drivers.length > 0 && (
            <div className="mb-8">
              <SectionLabel>What&rsquo;s Driving This</SectionLabel>
              <DriverList
                drivers={pred.drivers}
                homeTeam={match.home_team.short_name}
                awayTeam={match.away_team.short_name}
              />
            </div>
          )}

          {pred.scoreline_distribution && pred.scoreline_distribution.length > 0 && (
            <div className="mb-8">
              <SectionLabel>Scoreline Distribution</SectionLabel>
              <ScorelineGrid scorelines={pred.scoreline_distribution} />
            </div>
          )}
        </>
      ) : (
        <div className="surface p-8 text-sm text-ink/55">
          No prediction available for this match yet. Run{' '}
          <code className="font-mono">make train</code> to generate one.
        </div>
      )}
    </div>
  );
}

function computeMarketImplied(
  oh: number | null,
  od: number | null,
  oa: number | null
): { home: number; draw: number; away: number } | null {
  if (!oh || !od || !oa || oh <= 1 || od <= 1 || oa <= 1) return null;
  const raw = [1 / oh, 1 / od, 1 / oa];
  const sum = raw.reduce((a, b) => a + b, 0);
  return { home: raw[0] / sum, draw: raw[1] / sum, away: raw[2] / sum };
}

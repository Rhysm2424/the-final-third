'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import type { MatchSummary } from '@/lib/types';
import { cn, formatKickoff, formatProb } from '@/lib/utils';

interface FixtureRowProps {
  match: MatchSummary;
  index: number;
}

export function FixtureRow({ match, index }: FixtureRowProps) {
  const { time } = formatKickoff(match.kickoff);
  const probs = {
    home: match.prob_home,
    draw: match.prob_draw,
    away: match.prob_away,
  };
  const best = bestKey(probs);

  const isFinished = match.status === 'FINISHED';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index * 0.04, 0.4) }}
    >
      <Link
        href={`/match/${match.id}`}
        className="group grid grid-cols-[64px_1fr_auto] items-center gap-4 border-b border-line py-4 transition-colors hover:bg-paper-subtle"
      >
        <div className="font-mono text-sm text-ink/70">
          <div>{isFinished ? 'FT' : time}</div>
          <div className="label-mono mt-0.5">{match.competition.code}</div>
        </div>

        <div className="font-serif text-lg leading-tight sm:text-xl">
          <span className="font-semibold">{match.home_team.short_name}</span>
          <span className="mx-2 italic text-ink/40">v</span>
          <span className="font-semibold">{match.away_team.short_name}</span>
          {isFinished && match.home_score !== null && match.away_score !== null && (
            <span className="ml-3 font-mono text-sm text-ink/60">
              {match.home_score}–{match.away_score}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <ProbPill label="H" value={probs.home} best={best === 'home'} />
          <ProbPill label="D" value={probs.draw} best={best === 'draw'} />
          <ProbPill label="A" value={probs.away} best={best === 'away'} />
        </div>
      </Link>
    </motion.div>
  );
}

function ProbPill({
  label,
  value,
  best,
}: {
  label: string;
  value: number | null;
  best: boolean;
}) {
  return (
    <div className="min-w-[44px] text-center">
      <div className="label-mono mb-0.5">{label}</div>
      <div
        className={cn(
          'font-serif text-base font-semibold sm:text-lg',
          best && value !== null ? 'text-navy' : 'text-ink/80'
        )}
      >
        {formatProb(value)}
      </div>
    </div>
  );
}

function bestKey(p: { home: number | null; draw: number | null; away: number | null }): string | null {
  const entries = Object.entries(p).filter(([, v]) => v !== null) as [string, number][];
  if (entries.length === 0) return null;
  return entries.sort((a, b) => b[1] - a[1])[0][0];
}

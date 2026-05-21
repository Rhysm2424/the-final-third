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

  const pickColor =
    best === 'home'
      ? 'bg-navy'
      : best === 'draw'
        ? 'bg-ink-mid'
        : best === 'away'
          ? 'bg-signal-red'
          : 'bg-line';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index * 0.04, 0.4) }}
    >
      <Link
        href={`/match/${match.id}`}
        className="group relative grid grid-cols-[6px_64px_1fr_auto] items-center gap-x-4 border-b border-line py-4 pl-1 pr-2 transition-colors hover:bg-paper"
      >
        <span
          className={cn(
            'h-9 w-1 rounded-sm transition-all group-hover:h-11',
            pickColor
          )}
        />
        <div className="font-mono text-sm text-ink/70">
          <div className="tabular-nums">{isFinished ? 'FT' : time}</div>
          <div className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.12em] text-ink/45">
            {match.competition.code}
          </div>
        </div>

        <div className="font-serif text-lg leading-tight sm:text-xl">
          <span className={cn('font-semibold', best === 'home' && 'text-navy')}>
            {match.home_team.short_name}
          </span>
          <span className="mx-2 italic text-ink/35">v</span>
          <span className={cn('font-semibold', best === 'away' && 'text-signal-red')}>
            {match.away_team.short_name}
          </span>
          {isFinished && match.home_score !== null && match.away_score !== null && (
            <span className="ml-3 font-mono text-sm font-medium tabular-nums text-ink/55">
              {match.home_score}–{match.away_score}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <ProbPill label="H" value={probs.home} best={best === 'home'} variant="home" />
          <ProbPill label="D" value={probs.draw} best={best === 'draw'} variant="draw" />
          <ProbPill label="A" value={probs.away} best={best === 'away'} variant="away" />
        </div>
      </Link>
    </motion.div>
  );
}

function ProbPill({
  label,
  value,
  best,
  variant,
}: {
  label: string;
  value: number | null;
  best: boolean;
  variant: 'home' | 'draw' | 'away';
}) {
  const bestClass =
    variant === 'home'
      ? 'text-navy'
      : variant === 'away'
        ? 'text-signal-red'
        : 'text-ink';

  return (
    <div className="min-w-[44px] text-center">
      <div className="font-mono text-[9px] uppercase tracking-[0.12em] text-ink/40">
        {label}
      </div>
      <div
        className={cn(
          'mt-0.5 font-serif text-base tabular-nums sm:text-lg',
          best ? cn('font-semibold', bestClass) : 'font-medium text-ink/70'
        )}
      >
        {formatProb(value)}
      </div>
    </div>
  );
}

function bestKey(p: {
  home: number | null;
  draw: number | null;
  away: number | null;
}): string | null {
  const entries = Object.entries(p).filter(([, v]) => v !== null) as [string, number][];
  if (entries.length === 0) return null;
  return entries.sort((a, b) => b[1] - a[1])[0][0];
}

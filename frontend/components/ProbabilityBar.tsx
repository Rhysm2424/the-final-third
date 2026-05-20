'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ProbabilityBarProps {
  homeLabel: string;
  awayLabel: string;
  probHome: number;
  probDraw: number;
  probAway: number;
  marketImplied?: { home: number; draw: number; away: number } | null;
}

export function ProbabilityBar({
  homeLabel,
  awayLabel,
  probHome,
  probDraw,
  probAway,
  marketImplied,
}: ProbabilityBarProps) {
  // Normalise just in case (rounding)
  const total = probHome + probDraw + probAway;
  const ph = (probHome / total) * 100;
  const pd = (probDraw / total) * 100;
  const pa = (probAway / total) * 100;

  return (
    <div>
      <div className="flex h-16 overflow-hidden rounded-md border border-line">
        <Segment
          width={ph}
          label={homeLabel}
          value={probHome}
          color="bg-navy text-cream"
          delay={0}
        />
        <Segment
          width={pd}
          label="Draw"
          value={probDraw}
          color="bg-ink-mid text-cream"
          delay={0.08}
        />
        <Segment
          width={pa}
          label={awayLabel}
          value={probAway}
          color="bg-signal-red text-cream"
          delay={0.16}
        />
      </div>
      {marketImplied && (
        <div className="label-mono mt-2 flex flex-wrap justify-between gap-2">
          <span>
            Market implied: {Math.round(marketImplied.home * 100)}% /{' '}
            {Math.round(marketImplied.draw * 100)}% /{' '}
            {Math.round(marketImplied.away * 100)}%
          </span>
          <ModelEdge model={probHome} market={marketImplied.home} home={homeLabel} away={awayLabel} modelAway={probAway} marketAway={marketImplied.away} />
        </div>
      )}
    </div>
  );
}

function Segment({
  width,
  label,
  value,
  color,
  delay,
}: {
  width: number;
  label: string;
  value: number;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ flexBasis: '0%' }}
      animate={{ flexBasis: `${width}%` }}
      transition={{ duration: 0.8, delay, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        'flex min-w-0 flex-col items-center justify-center px-1',
        color
      )}
    >
      <div className="font-serif text-xl font-semibold leading-none">
        {Math.round(value * 100)}%
      </div>
      <div className="label-mono-on-navy mt-1 truncate">{label}</div>
    </motion.div>
  );
}

function ModelEdge({
  model,
  market,
  home,
  away,
  modelAway,
  marketAway,
}: {
  model: number;
  market: number;
  home: string;
  away: string;
  modelAway: number;
  marketAway: number;
}) {
  const homeEdge = (model - market) * 100;
  const awayEdge = (modelAway - marketAway) * 100;
  const absH = Math.abs(homeEdge);
  const absA = Math.abs(awayEdge);
  if (absH < 1.5 && absA < 1.5) return <span>Aligned with market</span>;
  if (absH >= absA) {
    const sign = homeEdge > 0 ? '+' : '−';
    return (
      <span>
        Model edge: {sign}
        {absH.toFixed(1)}pp {home}
      </span>
    );
  }
  const sign = awayEdge > 0 ? '+' : '−';
  return (
    <span>
      Model edge: {sign}
      {absA.toFixed(1)}pp {away}
    </span>
  );
}

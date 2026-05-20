'use client';

import { motion } from 'framer-motion';
import type { Driver } from '@/lib/types';
import { cn } from '@/lib/utils';

interface DriverListProps {
  drivers: Driver[];
  homeTeam: string;
  awayTeam: string;
}

export function DriverList({ drivers, homeTeam, awayTeam }: DriverListProps) {
  return (
    <div className="divide-y divide-line">
      {drivers.map((d, i) => (
        <motion.div
          key={`${d.label}-${i}`}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.08 * i }}
          className="grid grid-cols-[1fr_auto] items-center gap-4 py-3"
        >
          <div>
            <div className="font-serif text-base">{d.label}</div>
            <div className="mt-0.5 text-xs italic text-ink/55">{d.detail}</div>
          </div>
          <DriverImpact driver={d} homeTeam={homeTeam} awayTeam={awayTeam} />
        </motion.div>
      ))}
    </div>
  );
}

function DriverImpact({
  driver,
  homeTeam,
  awayTeam,
}: {
  driver: Driver;
  homeTeam: string;
  awayTeam: string;
}) {
  if (driver.direction === 'neutral') {
    return (
      <span className="rounded-sm bg-cream-200 px-2.5 py-1 font-mono text-[11px] font-semibold text-ink/60">
        context only
      </span>
    );
  }
  const sign = driver.impact_pp > 0 ? '+' : '';
  const teamLabel = driver.direction === 'home' ? homeTeam : awayTeam;
  return (
    <span
      className={cn(
        'rounded-sm px-2.5 py-1 font-mono text-[11px] font-semibold',
        driver.direction === 'home'
          ? 'bg-navy/10 text-navy'
          : 'bg-signal-red/10 text-signal-red'
      )}
    >
      {sign}
      {driver.impact_pp.toFixed(1)}pp {teamLabel}
    </span>
  );
}

'use client';

import { motion } from 'framer-motion';
import type { ScorelineProb } from '@/lib/types';

interface ScorelineGridProps {
  scorelines: ScorelineProb[];
}

export function ScorelineGrid({ scorelines }: ScorelineGridProps) {
  if (!scorelines.length) return null;
  const max = scorelines[0].prob;

  return (
    <div className="grid grid-cols-3 gap-1 sm:grid-cols-6">
      {scorelines.map((s, i) => {
        const fillHeight = (s.prob / max) * 100;
        return (
          <motion.div
            key={`${s.home}-${s.away}-${i}`}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.04 * i }}
            className="relative flex aspect-[1.4] flex-col items-center justify-center overflow-hidden rounded border border-line bg-paper"
          >
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${fillHeight}%` }}
              transition={{ duration: 0.6, delay: 0.04 * i + 0.2 }}
              className="absolute inset-x-0 bottom-0 bg-signal-gold/30"
            />
            <div className="relative z-10 font-serif text-base font-semibold">
              {s.home}–{s.away}
            </div>
            <div className="relative z-10 mt-0.5 font-mono text-[10px] text-ink/55">
              {(s.prob * 100).toFixed(1)}%
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

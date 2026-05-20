'use client';

import { motion } from 'framer-motion';
import type { Insight } from '@/lib/types';
import { cn } from '@/lib/utils';

const KIND_LABEL: Record<string, string> = {
  player_streak: 'Player',
  team_form: 'Team',
  historic_record: 'Historic',
  tactical_shift: 'Tactical',
};

const KIND_CLASS: Record<string, string> = {
  player_streak: 'bg-signal-green/15 text-signal-green',
  team_form: 'bg-signal-gold/25 text-ink',
  historic_record: 'bg-cream-200 text-ink/70',
  tactical_shift: 'bg-navy/10 text-navy',
};

export function InsightCard({ insight, index }: { insight: Insight; index: number }) {
  const tag = KIND_LABEL[insight.kind] ?? insight.kind;
  const tagClass = KIND_CLASS[insight.kind] ?? 'bg-cream-200 text-ink/60';

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: Math.min(0.06 * index, 0.45) }}
      className="surface mb-3.5 px-6 py-5"
    >
      <div className="mb-3 flex items-center gap-2.5">
        <span
          className={cn(
            'rounded-sm px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider',
            tagClass
          )}
        >
          {tag}
        </span>
        {insight.notability >= 80 && (
          <span className="rounded-sm bg-signal-red/15 px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-signal-red">
            Hot
          </span>
        )}
        <span className="ml-auto font-mono text-[10px] text-ink/40">
          Notability {Math.round(insight.notability)}
        </span>
      </div>

      <h3 className="display-serif mb-2 text-lg leading-snug sm:text-xl">
        {insight.headline}
      </h3>
      <p className="mb-3 text-sm leading-relaxed text-ink/65">{insight.detail}</p>

      <div className="flex flex-wrap gap-x-5 gap-y-1 border-t border-line pt-3 font-mono text-[11px] text-ink/55">
        {Object.entries(insight.data)
          .slice(0, 4)
          .map(([k, v]) => (
            <span key={k}>
              {humanise(k)}: <strong className="font-semibold text-ink">{format(v)}</strong>
            </span>
          ))}
        {!insight.is_weighted && (
          <span className="italic text-ink/45">not weighted</span>
        )}
      </div>
    </motion.article>
  );
}

function humanise(key: string): string {
  return key.replace(/_/g, ' ');
}

function format(v: unknown): string {
  if (typeof v === 'number') return v % 1 === 0 ? String(v) : v.toFixed(2);
  if (v === null || v === undefined) return '—';
  return String(v);
}

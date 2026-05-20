'use client';

import { motion } from 'framer-motion';

export interface StatCellProps {
  label: string;
  value: string;
  sub?: string;
}

export function StatRow({ cells }: { cells: StatCellProps[] }) {
  return (
    <div className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-line bg-line sm:grid-cols-3">
      {cells.map((c, i) => (
        <StatCell key={c.label} {...c} index={i} />
      ))}
    </div>
  );
}

function StatCell({ label, value, sub, index }: StatCellProps & { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 + index * 0.05 }}
      className="bg-paper px-5 py-4"
    >
      <div className="label-mono mb-1.5">{label}</div>
      <div className="display-serif text-2xl">
        {value}
        {sub && <span className="ml-1 font-serif text-base italic text-ink/50">{sub}</span>}
      </div>
    </motion.div>
  );
}

'use client';

import { motion } from 'framer-motion';

interface PageHeaderProps {
  kicker?: string;
  title: string;
  dek?: string;
}

export function PageHeader({ kicker, title, dek }: PageHeaderProps) {
  return (
    <div className="mb-10">
      {kicker && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-3 inline-flex items-center gap-2.5"
        >
          <span className="h-px w-6 bg-navy" />
          <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-navy">
            {kicker}
          </span>
        </motion.div>
      )}
      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.05 }}
        className="display-serif text-4xl leading-[1.02] tracking-tight sm:text-5xl"
      >
        {title}
      </motion.h1>
      {dek && (
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mt-4 max-w-[600px] font-serif text-base italic leading-relaxed text-ink/65 sm:text-lg"
        >
          {dek}
        </motion.p>
      )}
    </div>
  );
}

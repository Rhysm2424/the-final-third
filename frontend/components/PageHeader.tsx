'use client';

import { motion } from 'framer-motion';

interface PageHeaderProps {
  kicker?: string;
  title: string;
  dek?: string;
}

export function PageHeader({ kicker, title, dek }: PageHeaderProps) {
  return (
    <div className="mb-8">
      {kicker && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="label-mono mb-2 text-navy"
        >
          {kicker}
        </motion.div>
      )}
      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.05 }}
        className="display-serif text-4xl leading-[1.05] sm:text-5xl"
      >
        {title}
      </motion.h1>
      {dek && (
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mt-3 max-w-[640px] font-serif text-base italic text-ink/70 sm:text-lg"
        >
          {dek}
        </motion.p>
      )}
    </div>
  );
}

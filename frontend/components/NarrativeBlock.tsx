'use client';

import { motion } from 'framer-motion';

export function NarrativeBlock({ text }: { text: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="surface border-l-4 border-l-navy px-7 py-6"
    >
      <p className="font-serif text-base leading-relaxed sm:text-lg">{text}</p>
      <div className="label-mono mt-4 border-t border-line pt-3">
        Generated from structured signals · No editorial speculation
      </div>
    </motion.div>
  );
}

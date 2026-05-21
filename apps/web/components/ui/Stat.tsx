'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Card, CardHeader } from './Card';

export function Stat({
  title,
  value,
  hint,
  delta,
  accent,
}: {
  title: string;
  value: number | string;
  hint?: string;
  delta?: string;
  accent?: 'accent' | 'success' | 'warning' | 'danger';
}) {
  const numeric = typeof value === 'number';
  const [displayed, setDisplayed] = useState(numeric ? 0 : value);

  useEffect(() => {
    if (!numeric) return;
    const target = value as number;
    let frame = 0;
    const duration = 28;
    const id = setInterval(() => {
      frame += 1;
      const t = Math.min(1, frame / duration);
      setDisplayed(Math.round(target * (1 - Math.pow(1 - t, 3))));
      if (frame >= duration) clearInterval(id);
    }, 16);
    return () => clearInterval(id);
  }, [value, numeric]);

  const accentClass =
    accent === 'success'
      ? 'text-success'
      : accent === 'warning'
        ? 'text-warning'
        : accent === 'danger'
          ? 'text-danger'
          : 'text-accent-glow';

  return (
    <Card className="overflow-hidden">
      <CardHeader title={title} hint={hint} />
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="px-5 pb-5 pt-3"
      >
        <div className={`text-4xl font-semibold ${accentClass}`}>{displayed}</div>
        {delta && <div className="mt-1 text-xs text-gray-500">{delta}</div>}
      </motion.div>
    </Card>
  );
}

'use client';

import { motion } from 'framer-motion';
import { Clock } from 'lucide-react';
import type { ScheduledBlock } from '@/lib/api';
import { cn } from '@/lib/cn';

const HOUR_START = 6;
const HOUR_END = 23;
const ROW_HEIGHT = 56; // px per hour
const TOTAL_HOURS = HOUR_END - HOUR_START;

const PRIORITY_COLORS: Record<string, string> = {
  P0: 'from-danger/40 to-danger/10 border-danger/50',
  P1: 'from-warning/40 to-warning/10 border-warning/50',
  P2: 'from-accent/40 to-accent/10 border-accent/50',
  P3: 'from-bg-subtle to-bg-card border-border',
  P4: 'from-bg-subtle to-bg-card border-border',
};

function minutesFromDay(iso: string) {
  const d = new Date(iso);
  return d.getHours() * 60 + d.getMinutes();
}

export function ScheduleTimeline({ blocks, compact = false }: { blocks: ScheduledBlock[]; compact?: boolean }) {
  const totalMinutes = TOTAL_HOURS * 60;
  const hours = Array.from({ length: TOTAL_HOURS + 1 }, (_, i) => HOUR_START + i);

  return (
    <div className="relative" style={{ height: TOTAL_HOURS * ROW_HEIGHT }}>
      {/* hour gridlines */}
      <div className="absolute inset-0 grid" style={{ gridTemplateRows: `repeat(${TOTAL_HOURS}, ${ROW_HEIGHT}px)` }}>
        {hours.slice(0, -1).map((h) => (
          <div key={h} className="relative border-t border-border first:border-t-0">
            <span className="absolute -top-2 left-0 -translate-y-1/2 bg-bg px-1 font-mono text-[10px] text-gray-500">
              {String(h).padStart(2, '0')}:00
            </span>
          </div>
        ))}
      </div>

      {/* now indicator */}
      <NowIndicator totalMinutes={totalMinutes} />

      {/* blocks */}
      <div className="absolute inset-y-0 left-12 right-2">
        {blocks.length === 0 && (
          <div className="absolute inset-0 grid place-items-center">
            <div className="rounded-xl border border-dashed border-border px-6 py-8 text-center text-sm text-gray-500">
              No plan yet — нажмите «Generate plan» или сначала добавьте задачи.
            </div>
          </div>
        )}
        {blocks.map((b, i) => {
          const startMin = minutesFromDay(b.start) - HOUR_START * 60;
          const endMin = minutesFromDay(b.end) - HOUR_START * 60;
          const top = (Math.max(0, startMin) / totalMinutes) * 100;
          const height = (Math.max(15, endMin - startMin) / totalMinutes) * 100;
          return (
            <motion.div
              key={b.task_id + i}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04, duration: 0.3 }}
              className={cn(
                'absolute left-0 right-0 overflow-hidden rounded-xl border bg-gradient-to-br px-3 py-2 shadow-card backdrop-blur',
                PRIORITY_COLORS[b.priority] ?? PRIORITY_COLORS.P3,
                b.overflow && 'ring-1 ring-danger/60',
              )}
              style={{ top: `${top}%`, height: `${height}%`, minHeight: 36 }}
            >
              <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-gray-300">
                <span>{b.priority}</span>
                <span className="flex items-center gap-1 text-gray-400">
                  <Clock size={10} />
                  {new Date(b.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className={cn('mt-1 font-medium', compact ? 'text-xs' : 'text-sm')}>{b.title}</div>
              {b.overflow && (
                <div className="mt-1 text-[10px] uppercase tracking-wider text-danger">overflow</div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function NowIndicator({ totalMinutes }: { totalMinutes: number }) {
  const now = new Date();
  const minutes = now.getHours() * 60 + now.getMinutes() - HOUR_START * 60;
  if (minutes < 0 || minutes > totalMinutes) return null;
  const top = (minutes / totalMinutes) * 100;
  return (
    <div
      className="pointer-events-none absolute left-10 right-2 z-10"
      style={{ top: `${top}%` }}
      aria-hidden
    >
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-accent-glow shadow-glow" />
        <span className="h-px flex-1 bg-accent-glow/60" />
      </div>
    </div>
  );
}

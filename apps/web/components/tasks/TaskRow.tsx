'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Check, Circle, Clock, Flame, Split, AlertTriangle } from 'lucide-react';
import { tasksApi, type Task } from '@/lib/api';
import { cn } from '@/lib/cn';

const priorityStyles: Record<string, string> = {
  P0: 'border-danger/40 bg-danger/10 text-danger',
  P1: 'border-warning/40 bg-warning/10 text-warning',
  P2: 'border-accent/40 bg-accent/10 text-accent-glow',
  P3: 'border-border bg-bg-subtle text-gray-400',
  P4: 'border-border bg-bg-subtle text-gray-500',
};

function dueLabel(due: string | null) {
  if (!due) return null;
  const d = new Date(due);
  const diff = (d.getTime() - Date.now()) / (1000 * 60 * 60);
  if (diff < 0) return `${Math.round(-diff)}h overdue`;
  if (diff < 24) return `${Math.round(diff)}h`;
  return `${Math.round(diff / 24)}d`;
}

export function TaskRow({ task }: { task: Task }) {
  const qc = useQueryClient();
  const complete = useMutation({
    mutationFn: () => tasksApi.complete(task.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const decompose = useMutation({
    mutationFn: () => tasksApi.decompose(task.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const isDone = task.status === 'done';
  const due = dueLabel(task.due_date);
  const overdue = !!due && due.includes('overdue');
  
  // Procrastination nudge threshold
  const isProcrastinated = task.procrastination_score > 0.3;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className={cn(
        'group flex flex-col gap-2 rounded-xl border border-border bg-bg-card/60 px-4 py-3 transition hover:border-border-strong hover:bg-bg-card',
        isDone && 'opacity-50',
        isProcrastinated && 'border-warning/30 bg-warning/5',
      )}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={() => !isDone && complete.mutate()}
          className={cn(
            'grid h-6 w-6 place-items-center rounded-full border transition shrink-0',
            isDone
              ? 'border-success/60 bg-success/20 text-success'
              : 'border-border text-gray-500 hover:border-accent hover:text-accent-glow',
          )}
          aria-label="complete"
        >
          {isDone ? <Check size={12} /> : <Circle size={10} className="opacity-0 group-hover:opacity-100" />}
        </button>

        <div className="min-w-0 flex-1">
          <div className={cn('truncate text-sm flex items-center gap-2', isDone && 'line-through')}>
            {task.title}
            {isProcrastinated && !isDone && (
              <span className="text-warning flex items-center gap-1 text-[10px] uppercase font-bold tracking-widest bg-warning/10 px-1.5 py-0.5 rounded">
                <AlertTriangle size={10} /> Stuck
              </span>
            )}
          </div>
          {task.description && (
            <div className="mt-0.5 line-clamp-1 text-xs text-gray-500">{task.description}</div>
          )}
        </div>

        <span
          className={cn(
            'rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider shrink-0',
            priorityStyles[task.priority] ?? priorityStyles.P3,
          )}
        >
          {task.priority}
        </span>

        {task.estimated_minutes != null && (
          <span className="flex items-center gap-1 text-[11px] text-gray-500 shrink-0">
            <Clock size={12} /> {task.estimated_minutes}m
          </span>
        )}

        {due && (
          <span
            className={cn(
              'flex items-center gap-1 text-[11px] shrink-0',
              overdue ? 'text-danger' : 'text-gray-400',
            )}
          >
            {overdue ? <Flame size={12} /> : <Clock size={12} />}
            {due}
          </span>
        )}
      </div>

      {/* Procrastination actions */}
      {isProcrastinated && !isDone && (
        <div className="pl-9 pr-2 py-1 flex items-center gap-4">
          <p className="text-[11px] text-white/50">
            This task has been delayed (score: {(task.procrastination_score * 100).toFixed(0)}%). 
            Try breaking it down to regain momentum.
          </p>
          <button
            onClick={() => decompose.mutate()}
            disabled={decompose.isPending}
            className="flex items-center gap-1 text-[11px] bg-accent/10 hover:bg-accent/20 text-accent px-2 py-1 rounded transition-colors ml-auto"
          >
            {decompose.isPending ? <Clock size={12} className="animate-spin" /> : <Split size={12} />}
            AI Micro-steps
          </button>
        </div>
      )}
    </motion.div>
  );
}

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { useState } from 'react';
import { tasksApi, type Task, type TaskStatus } from '@/lib/api';
import { cn } from '@/lib/cn';
import { Card, CardHeader } from '@/components/ui/Card';
import { TaskRow } from '@/components/tasks/TaskRow';
import { NewTaskForm } from '@/components/tasks/NewTaskForm';

const STATUSES: { id: TaskStatus | 'all'; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'inbox', label: 'Inbox' },
  { id: 'planned', label: 'Planned' },
  { id: 'active', label: 'Active' },
  { id: 'done', label: 'Done' },
  { id: 'snoozed', label: 'Snoozed' },
];

export default function TasksPage() {
  const [filter, setFilter] = useState<TaskStatus | 'all'>('all');
  const qc = useQueryClient();

  const q = useQuery({
    queryKey: ['tasks', 'list', filter],
    queryFn: () => {
      const p = new URLSearchParams();
      if (filter !== 'all') p.append('status', filter);
      p.set('limit', '100');
      return tasksApi.list(p);
    },
  });

  const reprio = useMutation({
    mutationFn: () => tasksApi.reprioritize(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const items: Task[] = q.data?.items ?? [];
  const grouped = items.reduce<Record<string, Task[]>>((acc, t) => {
    (acc[t.priority] ||= []).push(t);
    return acc;
  }, {});
  const order = ['P0', 'P1', 'P2', 'P3', 'P4'];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Tasks</p>
          <h1 className="mt-2 text-3xl font-semibold">All tasks</h1>
          <p className="mt-1 text-sm text-gray-400">
            {q.data?.total ?? 0} total · grouped by NeuroPlan priority bucket.
          </p>
        </div>
        <button
          onClick={() => reprio.mutate()}
          disabled={reprio.isPending}
          className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow transition hover:border-accent disabled:opacity-50"
        >
          <Sparkles size={14} /> Recompute priorities
        </button>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        {STATUSES.map((s) => (
          <button
            key={s.id}
            onClick={() => setFilter(s.id)}
            className={cn(
              'rounded-full border px-3 py-1 text-xs transition',
              filter === s.id
                ? 'border-accent/60 bg-accent/15 text-accent-glow'
                : 'border-border bg-bg-card/60 text-gray-400 hover:border-border-strong hover:text-gray-100',
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      <NewTaskForm />

      {q.isLoading && <div className="text-sm text-gray-500">Loading…</div>}

      <div className="space-y-6">
        {order.map((bucket) => {
          const rows = grouped[bucket];
          if (!rows?.length) return null;
          return (
            <Card key={bucket}>
              <CardHeader title={bucket} hint={`${rows.length} task${rows.length > 1 ? 's' : ''}`} />
              <div className="space-y-2 px-5 pb-5 pt-3">
                <AnimatePresence>
                  {rows.map((t) => <TaskRow key={t.id} task={t} />)}
                </AnimatePresence>
              </div>
            </Card>
          );
        })}

        {!q.isLoading && items.length === 0 && (
          <Card>
            <div className="px-5 py-10 text-center text-sm text-gray-500">
              Нет задач в этой группе. Добавьте задачу выше или нажмите
              «Recompute priorities».
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

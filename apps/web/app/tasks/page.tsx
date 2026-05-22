'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { LayoutList, Columns3, Sparkles, GripVertical } from 'lucide-react';
import { useState } from 'react';
import { tasksApi, type Page, type Task, type TaskStatus } from '@/lib/api';
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

const KANBAN_COLUMNS: { id: TaskStatus; label: string; accent: string }[] = [
  { id: 'inbox', label: 'Inbox', accent: 'text-gray-400' },
  { id: 'planned', label: 'Planned', accent: 'text-accent-glow' },
  { id: 'active', label: 'Active', accent: 'text-warning' },
  { id: 'done', label: 'Done', accent: 'text-success' },
];

type View = 'list' | 'kanban';

export default function TasksPage() {
  const [view, setView] = useState<View>('list');
  const [filter, setFilter] = useState<TaskStatus | 'all'>('all');
  const qc = useQueryClient();

  const reprio = useMutation({
    mutationFn: () => tasksApi.reprioritize(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Tasks</p>
          <h1 className="mt-2 text-3xl font-semibold">All tasks</h1>
          <p className="mt-1 text-sm text-gray-400">
            {view === 'list'
              ? 'Сгруппировано по приоритету AI Planner.'
              : 'Перетаскивайте карточки между колонками — меняется статус задачи.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-border bg-bg-card/60 p-0.5">
            <ViewButton active={view === 'list'} onClick={() => setView('list')} icon={LayoutList} label="List" />
            <ViewButton
              active={view === 'kanban'}
              onClick={() => setView('kanban')}
              icon={Columns3}
              label="Kanban"
            />
          </div>
          <button
            onClick={() => reprio.mutate()}
            disabled={reprio.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow transition hover:border-accent disabled:opacity-50"
          >
            <Sparkles size={14} /> Recompute priorities
          </button>
        </div>
      </header>

      <NewTaskForm />

      {view === 'list' ? (
        <ListView filter={filter} setFilter={setFilter} />
      ) : (
        <KanbanView />
      )}
    </div>
  );
}

function ViewButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ComponentType<{ size?: number }>;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs transition',
        active ? 'bg-accent/15 text-accent-glow' : 'text-gray-400 hover:text-gray-100',
      )}
    >
      <Icon size={14} />
      {label}
    </button>
  );
}

function ListView({
  filter,
  setFilter,
}: {
  filter: TaskStatus | 'all';
  setFilter: (f: TaskStatus | 'all') => void;
}) {
  const q = useQuery({
    queryKey: ['tasks', 'list', filter],
    queryFn: () => {
      const p = new URLSearchParams();
      if (filter !== 'all') p.append('status', filter);
      p.set('limit', '100');
      return tasksApi.list(p);
    },
  });

  const items: Task[] = q.data?.items ?? [];
  const grouped = items.reduce<Record<string, Task[]>>((acc, t) => {
    (acc[t.priority] ||= []).push(t);
    return acc;
  }, {});
  const order = ['P0', 'P1', 'P2', 'P3', 'P4'];

  return (
    <>
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
                  {rows.map((t) => (
                    <TaskRow key={t.id} task={t} />
                  ))}
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
    </>
  );
}

function KanbanView() {
  const qc = useQueryClient();
  const [dragId, setDragId] = useState<string | null>(null);
  const [overCol, setOverCol] = useState<TaskStatus | null>(null);
  const queryKey = ['tasks', 'kanban'];

  const q = useQuery({
    queryKey,
    queryFn: () => tasksApi.list(new URLSearchParams({ limit: '200' })),
  });

  const moveStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) =>
      tasksApi.update(id, { status }),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey });
      const prev = qc.getQueryData<Page<Task>>(queryKey);
      qc.setQueryData<Page<Task>>(queryKey, (old) =>
        old
          ? { ...old, items: old.items.map((t) => (t.id === id ? { ...t, status } : t)) }
          : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(queryKey, ctx.prev);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const items: Task[] = q.data?.items ?? [];
  const byStatus = (s: TaskStatus) =>
    items
      .filter((t) => t.status === s)
      .sort((a, b) => b.priority_score - a.priority_score);

  const handleDrop = (status: TaskStatus) => {
    setOverCol(null);
    if (!dragId) return;
    const task = items.find((t) => t.id === dragId);
    setDragId(null);
    if (!task || task.status === status) return;
    moveStatus.mutate({ id: task.id, status });
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {KANBAN_COLUMNS.map((col) => {
        const rows = byStatus(col.id);
        return (
          <div
            key={col.id}
            onDragOver={(e) => {
              e.preventDefault();
              if (overCol !== col.id) setOverCol(col.id);
            }}
            onDragLeave={() => setOverCol((c) => (c === col.id ? null : c))}
            onDrop={() => handleDrop(col.id)}
            className={cn(
              'flex min-h-[300px] flex-col rounded-2xl border border-border bg-bg-card/40 p-3 transition',
              overCol === col.id && 'ring-2 ring-accent/60',
            )}
          >
            <div className="mb-3 flex items-center justify-between px-1">
              <span className={cn('text-xs font-semibold uppercase tracking-wider', col.accent)}>
                {col.label}
              </span>
              <span className="rounded-full border border-border bg-bg-subtle px-2 py-0.5 text-[10px] text-gray-400">
                {rows.length}
              </span>
            </div>
            <div className="flex flex-1 flex-col gap-2">
              <AnimatePresence>
                {rows.map((t) => (
                  <motion.div
                    key={t.id}
                    layout
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    draggable
                    onDragStart={() => setDragId(t.id)}
                    onDragEnd={() => {
                      setDragId(null);
                      setOverCol(null);
                    }}
                    className={cn(
                      'group cursor-grab rounded-xl border border-border bg-bg-card px-3 py-2 shadow-card transition hover:border-border-strong active:cursor-grabbing',
                      dragId === t.id && 'opacity-40',
                    )}
                  >
                    <div className="flex items-start gap-2">
                      <GripVertical
                        size={13}
                        className="mt-0.5 shrink-0 text-gray-600 group-hover:text-gray-400"
                      />
                      <span className="min-w-0 flex-1 text-sm">{t.title}</span>
                      <span className="shrink-0 font-mono text-[10px] text-gray-500">
                        {t.priority}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {rows.length === 0 && (
                <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-border/60 text-[11px] text-gray-600">
                  drop here
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

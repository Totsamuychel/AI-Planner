'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, GripVertical } from 'lucide-react';
import { useState } from 'react';
import { tasksApi, type Page, type Task } from '@/lib/api';
import { cn } from '@/lib/cn';

type QuadrantId = 'do' | 'schedule' | 'delegate' | 'eliminate';

interface Quadrant {
  id: QuadrantId;
  title: string;
  subtitle: string;
  hint: string;
  importance: number;
  urgency: number;
  accent: string;
  ring: string;
}

// Drop targets write these (importance, urgency) onto the task.
const QUADRANTS: Quadrant[] = [
  {
    id: 'do',
    title: 'Do First',
    subtitle: 'Срочно · Важно',
    hint: 'Сделать немедленно',
    importance: 0.8,
    urgency: 0.8,
    accent: 'text-danger',
    ring: 'border-danger/30 bg-danger/5',
  },
  {
    id: 'schedule',
    title: 'Schedule',
    subtitle: 'Не срочно · Важно',
    hint: 'Запланировать время',
    importance: 0.8,
    urgency: 0.2,
    accent: 'text-accent-glow',
    ring: 'border-accent/30 bg-accent/5',
  },
  {
    id: 'delegate',
    title: 'Delegate',
    subtitle: 'Срочно · Не важно',
    hint: 'Делегировать / быстро закрыть',
    importance: 0.2,
    urgency: 0.8,
    accent: 'text-warning',
    ring: 'border-warning/30 bg-warning/5',
  },
  {
    id: 'eliminate',
    title: 'Eliminate',
    subtitle: 'Не срочно · Не важно',
    hint: 'Отказаться / в бэклог',
    importance: 0.2,
    urgency: 0.2,
    accent: 'text-gray-400',
    ring: 'border-border bg-bg-subtle/40',
  },
];

function quadrantOf(task: Task): QuadrantId {
  const important = task.importance_score >= 0.5;
  const urgent = task.urgency_score >= 0.5;
  if (important && urgent) return 'do';
  if (important && !urgent) return 'schedule';
  if (!important && urgent) return 'delegate';
  return 'eliminate';
}

const OPEN_STATUSES = ['inbox', 'planned', 'active'];

export default function MatrixPage() {
  const qc = useQueryClient();
  const [dragId, setDragId] = useState<string | null>(null);
  const [overQuad, setOverQuad] = useState<QuadrantId | null>(null);

  const queryKey = ['tasks', 'matrix'];
  const tasksQuery = useQuery({
    queryKey,
    queryFn: () => {
      const p = new URLSearchParams();
      OPEN_STATUSES.forEach((s) => p.append('status', s));
      p.set('limit', '200');
      return tasksApi.list(p);
    },
  });

  const move = useMutation({
    mutationFn: ({ id, importance, urgency }: { id: string; importance: number; urgency: number }) =>
      tasksApi.setScores(id, { importance_score: importance, urgency_score: urgency }),
    onMutate: async ({ id, importance, urgency }) => {
      await qc.cancelQueries({ queryKey });
      const prev = qc.getQueryData<Page<Task>>(queryKey);
      qc.setQueryData<Page<Task>>(queryKey, (old) =>
        old
          ? {
              ...old,
              items: old.items.map((t) =>
                t.id === id ? { ...t, importance_score: importance, urgency_score: urgency } : t,
              ),
            }
          : old,
      );
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(queryKey, ctx.prev);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const items = tasksQuery.data?.items ?? [];
  const grouped: Record<QuadrantId, Task[]> = {
    do: [],
    schedule: [],
    delegate: [],
    eliminate: [],
  };
  for (const t of items) grouped[quadrantOf(t)].push(t);
  for (const q of Object.keys(grouped) as QuadrantId[]) {
    grouped[q].sort((a, b) => b.priority_score - a.priority_score);
  }

  const handleDrop = (quad: Quadrant) => {
    setOverQuad(null);
    if (!dragId) return;
    const task = items.find((t) => t.id === dragId);
    setDragId(null);
    if (!task) return;
    if (quadrantOf(task) === quad.id) return; // no-op if same quadrant
    move.mutate({ id: task.id, importance: quad.importance, urgency: quad.urgency });
  };

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Prioritization</p>
        <h1 className="mt-2 text-3xl font-semibold">Матрица Эйзенхауэра</h1>
        <p className="mt-1 text-sm text-gray-400">
          {items.length} активных задач · перетаскивайте карточки между квадрантами —
          это меняет важность и срочность задачи.
        </p>
      </header>

      {tasksQuery.isLoading && <div className="text-sm text-gray-500">Загрузка…</div>}

      <div className="grid gap-4 md:grid-cols-2">
        {QUADRANTS.map((q) => (
          <div
            key={q.id}
            onDragOver={(e) => {
              e.preventDefault();
              if (overQuad !== q.id) setOverQuad(q.id);
            }}
            onDragLeave={() => setOverQuad((cur) => (cur === q.id ? null : cur))}
            onDrop={() => handleDrop(q)}
            className={cn(
              'flex min-h-[260px] flex-col rounded-2xl border p-4 transition',
              q.ring,
              overQuad === q.id && 'ring-2 ring-accent/60 scale-[1.01]',
            )}
          >
            <div className="mb-3 flex items-baseline justify-between">
              <div>
                <h2 className={cn('text-sm font-semibold uppercase tracking-wider', q.accent)}>
                  {q.title}
                </h2>
                <p className="text-[11px] text-gray-500">{q.subtitle}</p>
              </div>
              <span className="rounded-full border border-border bg-bg-card/60 px-2 py-0.5 text-[10px] text-gray-400">
                {grouped[q.id].length}
              </span>
            </div>

            <div className="flex flex-1 flex-col gap-2">
              <AnimatePresence>
                {grouped[q.id].map((t) => (
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
                      setOverQuad(null);
                    }}
                    className={cn(
                      'group flex cursor-grab items-center gap-2 rounded-xl border border-border bg-bg-card px-3 py-2 shadow-card transition hover:border-border-strong active:cursor-grabbing',
                      dragId === t.id && 'opacity-40',
                    )}
                  >
                    <GripVertical
                      size={14}
                      className="shrink-0 text-gray-600 group-hover:text-gray-400"
                    />
                    <span className="min-w-0 flex-1 truncate text-sm">{t.title}</span>
                    <span className="shrink-0 font-mono text-[10px] text-gray-500">
                      {t.priority}
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>

              {grouped[q.id].length === 0 && (
                <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-border/60 text-center text-[11px] text-gray-600">
                  {q.hint}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <p className="flex items-center gap-2 text-xs text-gray-500">
        <CheckCircle2 size={14} className="text-success" />
        Квадрант задачи вычисляется из её срочности и важности; перетаскивание
        мгновенно пересчитывает приоритет (P0–P4).
      </p>
    </div>
  );
}

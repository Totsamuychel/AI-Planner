'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, CalendarRange, Sparkles, type LucideIcon } from 'lucide-react';
import { useState } from 'react';
import { scheduleApi } from '@/lib/api';
import { cn } from '@/lib/cn';
import { Card, CardHeader } from '@/components/ui/Card';
import { ScheduleTimeline } from '@/components/schedule/Timeline';

type View = 'day' | 'week';

export default function CalendarPage() {
  const qc = useQueryClient();
  const [view, setView] = useState<View>('day');

  const today = useQuery({ queryKey: ['schedule', 'today'], queryFn: scheduleApi.today });
  const week = useQuery({
    queryKey: ['schedule', 'week'],
    queryFn: scheduleApi.week,
    enabled: view === 'week',
  });

  const generate = useMutation({
    mutationFn: scheduleApi.generate,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedule'] });
      qc.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
  const rebalance = useMutation({
    mutationFn: scheduleApi.rebalance,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedule'] });
      qc.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const plan = today.data;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Schedule</p>
          <h1 className="mt-2 text-3xl font-semibold" suppressHydrationWarning>
            {new Date().toLocaleDateString(undefined, {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
            })}
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            {view === 'day'
              ? `${plan?.blocks.length ?? 0} blocks · ${plan?.overflow_count ?? 0} overflow`
              : 'Запланированные задачи на 7 дней вперёд.'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-lg border border-border bg-bg-card/60 p-0.5">
            <ViewBtn active={view === 'day'} onClick={() => setView('day')} icon={CalendarDays} label="Day" />
            <ViewBtn active={view === 'week'} onClick={() => setView('week')} icon={CalendarRange} label="Week" />
          </div>
          <button
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow transition hover:border-accent disabled:opacity-50"
          >
            <Sparkles size={14} /> Generate plan
          </button>
          <button
            onClick={() => rebalance.mutate()}
            disabled={rebalance.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-bg-card/60 px-3 py-2 text-xs text-gray-300 transition hover:border-border-strong disabled:opacity-50"
          >
            <CalendarDays size={14} /> Rebalance
          </button>
        </div>
      </header>

      {view === 'day' ? (
        <Card className="px-5 pb-6 pt-5">
          <CardHeader title="Day timeline" hint="6:00 → 23:00 · powered by AI Planner scheduler" />
          <div className="mt-4">
            <ScheduleTimeline blocks={plan?.blocks ?? []} />
          </div>
        </Card>
      ) : (
        <WeekView days={week.data?.days ?? []} loading={week.isLoading} />
      )}
    </div>
  );
}

function ViewBtn({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: LucideIcon;
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

function WeekView({
  days,
  loading,
}: {
  days: { date: string; blocks: { task_id: string; title: string; priority: string; start: string }[] }[];
  loading: boolean;
}) {
  if (loading) return <div className="text-sm text-gray-500">Загрузка…</div>;

  const priorityDot: Record<string, string> = {
    P0: 'bg-danger',
    P1: 'bg-warning',
    P2: 'bg-accent',
    P3: 'bg-gray-500',
    P4: 'bg-gray-600',
  };

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
      {days.map((d) => {
        const date = new Date(d.date + 'T00:00:00');
        const isToday = d.date === new Date().toISOString().slice(0, 10);
        return (
          <div
            key={d.date}
            className={cn(
              'flex min-h-[220px] flex-col rounded-2xl border bg-bg-card/40 p-3',
              isToday ? 'border-accent/50' : 'border-border',
            )}
          >
            <div className="mb-2 flex items-baseline justify-between">
              <span
                className={cn(
                  'text-xs font-semibold uppercase tracking-wider',
                  isToday ? 'text-accent-glow' : 'text-gray-400',
                )}
                suppressHydrationWarning
              >
                {date.toLocaleDateString(undefined, { weekday: 'short' })}
              </span>
              <span className="text-[11px] text-gray-500" suppressHydrationWarning>
                {date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
              </span>
            </div>
            <div className="flex flex-1 flex-col gap-1.5">
              {d.blocks.length === 0 && (
                <div className="flex flex-1 items-center justify-center text-[11px] text-gray-600">
                  —
                </div>
              )}
              {d.blocks.map((b) => (
                <div
                  key={b.task_id}
                  className="rounded-lg border border-border bg-bg-card px-2.5 py-1.5"
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className={cn('h-1.5 w-1.5 shrink-0 rounded-full', priorityDot[b.priority] ?? 'bg-gray-500')}
                    />
                    <span className="text-[11px] text-gray-400" suppressHydrationWarning>
                      {new Date(b.start).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                  <div className="mt-0.5 line-clamp-2 text-xs">{b.title}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

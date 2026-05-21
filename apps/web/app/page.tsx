'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { analyticsApi, tasksApi, scheduleApi } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { Stat } from '@/components/ui/Stat';
import { Sparkline } from '@/components/ui/Sparkline';
import { TaskRow } from '@/components/tasks/TaskRow';
import { NewTaskForm } from '@/components/tasks/NewTaskForm';
import { ScheduleTimeline } from '@/components/schedule/Timeline';

export default function DashboardPage() {
  const analytics = useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: () => analyticsApi.dashboard(),
  });
  const top = useQuery({
    queryKey: ['tasks', 'top'],
    queryFn: () => {
      const p = new URLSearchParams();
      ['inbox', 'planned', 'active'].forEach((s) => p.append('status', s));
      p.set('limit', '6');
      return tasksApi.list(p);
    },
  });
  const todaySchedule = useQuery({
    queryKey: ['schedule', 'today'],
    queryFn: scheduleApi.today,
  });

  const totals = analytics.data?.totals;

  return (
    <div className="space-y-8">
      <motion.header
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Today</p>
        <h1 className="mt-2 text-4xl font-semibold">
          {new Date().toLocaleDateString(undefined, {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
          })}
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Plan your day with AI-assisted priorities — Phase&nbsp;1 is live.
        </p>
      </motion.header>

      <section className="grid gap-4 md:grid-cols-4">
        <Stat title="Open tasks" value={totals?.open ?? 0} hint="inbox + planned + active" />
        <Stat
          title="Overdue"
          value={totals?.overdue ?? 0}
          accent={(totals?.overdue ?? 0) > 0 ? 'danger' : 'success'}
        />
        <Stat
          title="Done today"
          value={totals?.completed_today ?? 0}
          accent="success"
        />
        <Stat title="Done · last 7d" value={totals?.completed_7d ?? 0} accent="accent" />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Top priorities"
            hint="Sorted by NeuroPlan priority score"
            right={
              <Link
                href="/tasks"
                className="text-xs text-accent-glow underline-offset-4 hover:underline"
              >
                Open all →
              </Link>
            }
          />
          <div className="space-y-2 px-5 pb-5 pt-3">
            <NewTaskForm />
            {top.isLoading && <div className="text-sm text-gray-500">Loading…</div>}
            {top.data?.items.length === 0 && (
              <div className="rounded-xl border border-dashed border-border px-4 py-8 text-center text-sm text-gray-500">
                Inbox is empty. Add your first task above.
              </div>
            )}
            {top.data?.items.map((t) => <TaskRow key={t.id} task={t} />)}
          </div>
        </Card>

        <Card>
          <CardHeader title="Completion · 7 days" hint="Tasks completed per day" />
          <div className="px-5 pb-5 pt-4">
            <Sparkline data={analytics.data?.completion_7d ?? []} />
          </div>
        </Card>
      </section>

      <section>
        <Card className="px-5 pb-6 pt-5">
          <CardHeader
            title="Today's schedule"
            hint="6:00 → 23:00"
            right={
              <Link
                href="/calendar"
                className="text-xs text-accent-glow underline-offset-4 hover:underline"
              >
                Open calendar →
              </Link>
            }
          />
          <div className="mt-4 max-h-[420px] overflow-y-auto">
            <ScheduleTimeline blocks={todaySchedule.data?.blocks ?? []} compact />
          </div>
        </Card>
      </section>
    </div>
  );
}

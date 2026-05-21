'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, Sparkles } from 'lucide-react';
import { scheduleApi } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/Card';
import { ScheduleTimeline } from '@/components/schedule/Timeline';

export default function CalendarPage() {
  const qc = useQueryClient();
  const today = useQuery({ queryKey: ['schedule', 'today'], queryFn: scheduleApi.today });

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
          <h1 className="mt-2 text-3xl font-semibold">
            {new Date().toLocaleDateString(undefined, {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
            })}
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            {plan?.blocks.length ?? 0} blocks · {plan?.overflow_count ?? 0} overflow
          </p>
        </div>
        <div className="flex gap-2">
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

      <Card className="px-5 pb-6 pt-5">
        <CardHeader title="Day timeline" hint="6:00 → 23:00 · powered by AI Planner scheduler" />
        <div className="mt-4">
          <ScheduleTimeline blocks={plan?.blocks ?? []} />
        </div>
      </Card>
    </div>
  );
}

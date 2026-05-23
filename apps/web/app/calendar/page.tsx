'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  CalendarDays,
  CalendarRange,
  ExternalLink,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { googleApi, type GoogleEvent } from '@/lib/api';
import { cn } from '@/lib/cn';
import { Card, CardHeader } from '@/components/ui/Card';
import { ScheduleTimeline } from '@/components/schedule/Timeline';

type View = 'day' | 'week';

interface NormalizedBlock {
  task_id: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
  priority_score: number;
  energy_type: null;
  start: string;
  end: string;
  overflow: boolean;
}

function eventStart(e: GoogleEvent): string | null {
  return e.start?.dateTime ?? e.start?.date ?? null;
}
function eventEnd(e: GoogleEvent): string | null {
  return e.end?.dateTime ?? e.end?.date ?? null;
}
function toBlock(e: GoogleEvent): NormalizedBlock | null {
  const s = eventStart(e);
  const en = eventEnd(e);
  if (!s || !en) return null;
  return {
    task_id: e.id,
    title: e.summary || '(без названия)',
    priority: 'P2',
    priority_score: 0.5,
    energy_type: null,
    start: s,
    end: en,
    overflow: false,
  };
}

export default function CalendarPage() {
  const qc = useQueryClient();
  const [view, setView] = useState<View>('day');

  const status = useQuery({ queryKey: ['google', 'status'], queryFn: googleApi.status });
  const connected = !!status.data?.connected;

  const today = useQuery({
    queryKey: ['google', 'events', 'day'],
    queryFn: () => googleApi.events(),
    enabled: connected && view === 'day',
  });

  const week = useQuery({
    queryKey: ['google', 'events', 'week'],
    queryFn: () => {
      const start = new Date();
      start.setHours(0, 0, 0, 0);
      const end = new Date(start);
      end.setDate(end.getDate() + 7);
      const p = new URLSearchParams({
        start: start.toISOString(),
        end: end.toISOString(),
      });
      return googleApi.events(p);
    },
    enabled: connected && view === 'week',
  });

  const aiPlan = useMutation({
    mutationFn: googleApi.aiPlan,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['google', 'events'] });
      qc.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const dayBlocks = (today.data?.events ?? [])
    .map(toBlock)
    .filter((b): b is NormalizedBlock => !!b);
  const weekEvents = week.data?.events ?? [];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Google Calendar</p>
          <h1 className="mt-2 text-3xl font-semibold" suppressHydrationWarning>
            {new Date().toLocaleDateString(undefined, {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
            })}
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            {connected
              ? view === 'day'
                ? `${dayBlocks.length} events today`
                : 'События на 7 дней вперёд'
              : 'Подключите Google Calendar в Settings, чтобы видеть события и пушить туда задачи.'}
          </p>
          {aiPlan.data && (
            <p className="mt-1 text-xs text-accent-glow">
              Создано событий в Google: {aiPlan.data.created} (skipped {aiPlan.data.skipped}).
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-lg border border-border bg-bg-card/60 p-0.5">
            <ViewBtn active={view === 'day'} onClick={() => setView('day')} icon={CalendarDays} label="Day" />
            <ViewBtn active={view === 'week'} onClick={() => setView('week')} icon={CalendarRange} label="Week" />
          </div>
          {connected ? (
            <button
              onClick={() => aiPlan.mutate()}
              disabled={aiPlan.isPending}
              className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow transition hover:border-accent disabled:opacity-50"
            >
              <Sparkles size={14} className={aiPlan.isPending ? 'animate-spin' : ''} />
              {aiPlan.isPending ? 'Планирую…' : 'AI план → Google'}
            </button>
          ) : (
            <Link
              href="/settings"
              className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow transition hover:border-accent"
            >
              <ExternalLink size={14} /> Connect Google
            </Link>
          )}
        </div>
      </header>

      {!connected && <NotConnectedHint configured={!!status.data?.configured} />}

      {connected && view === 'day' && (
        <Card className="px-5 pb-6 pt-5">
          <CardHeader title="Day timeline" hint="6:00 → 23:00 · Google Calendar events" />
          <div className="mt-4">
            <ScheduleTimeline blocks={dayBlocks} />
          </div>
        </Card>
      )}

      {connected && view === 'week' && (
        <WeekView events={weekEvents} loading={week.isLoading} />
      )}
    </div>
  );
}

function NotConnectedHint({ configured }: { configured: boolean }) {
  return (
    <Card className="px-5 py-8 text-center">
      <p className="text-sm text-gray-300">
        {configured
          ? 'Google OAuth настроен на бэкенде, но аккаунт ещё не подключён. Откройте Settings и нажмите «Connect Google Calendar».'
          : 'Google OAuth не настроен. В .env добавьте GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET, перезапустите api и подключитесь в Settings.'}
      </p>
      <p className="mt-2 text-xs text-gray-500">
        Инструкция: <code>docs/GOOGLE_CALENDAR.md</code>
      </p>
    </Card>
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

function WeekView({ events, loading }: { events: GoogleEvent[]; loading: boolean }) {
  if (loading) return <div className="text-sm text-gray-500">Загрузка…</div>;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    return d;
  });
  const byDay = new Map<string, GoogleEvent[]>(
    days.map((d) => [d.toISOString().slice(0, 10), []]),
  );
  for (const e of events) {
    const s = eventStart(e);
    if (!s) continue;
    const key = s.slice(0, 10);
    if (byDay.has(key)) byDay.get(key)!.push(e);
  }
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
      {days.map((d) => {
        const key = d.toISOString().slice(0, 10);
        const list = byDay.get(key) ?? [];
        const isToday = key === today.toISOString().slice(0, 10);
        return (
          <div
            key={key}
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
                {d.toLocaleDateString(undefined, { weekday: 'short' })}
              </span>
              <span className="text-[11px] text-gray-500" suppressHydrationWarning>
                {d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
              </span>
            </div>
            <div className="flex flex-1 flex-col gap-1.5">
              {list.length === 0 && (
                <div className="flex flex-1 items-center justify-center text-[11px] text-gray-600">
                  —
                </div>
              )}
              {list.map((e) => {
                const start = eventStart(e);
                return (
                  <a
                    key={e.id}
                    href={e.htmlLink || '#'}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="rounded-lg border border-border bg-bg-card px-2.5 py-1.5 transition hover:border-border-strong"
                  >
                    <div className="flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      <span className="text-[11px] text-gray-400" suppressHydrationWarning>
                        {start
                          ? new Date(start).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : 'all day'}
                      </span>
                    </div>
                    <div className="mt-0.5 line-clamp-2 text-xs">
                      {e.summary || '(без названия)'}
                    </div>
                  </a>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

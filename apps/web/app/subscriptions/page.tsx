'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { CalendarClock, Plus, Wallet, X } from 'lucide-react';
import { useState } from 'react';
import {
  subscriptionsApi,
  type BillingPeriod,
  type Subscription,
} from '@/lib/api';
import { cn } from '@/lib/cn';
import { Card, CardHeader } from '@/components/ui/Card';
import { Stat } from '@/components/ui/Stat';

const PERIODS: { value: BillingPeriod; label: string }[] = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'weekly', label: 'Weekly' },
];

function daysUntil(iso: string): number {
  const d = new Date(iso + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - today.getTime()) / 86_400_000);
}

function formatMoney(n: number, currency: string) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(n);
  } catch {
    return `${n.toFixed(2)} ${currency}`;
  }
}

export default function SubscriptionsPage() {
  const qc = useQueryClient();
  const list = useQuery({ queryKey: ['subscriptions'], queryFn: subscriptionsApi.list });
  const summary = useQuery({
    queryKey: ['subscriptions', 'summary'],
    queryFn: subscriptionsApi.summary,
  });

  const remove = useMutation({
    mutationFn: (id: string) => subscriptionsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['subscriptions'] }),
  });

  const items: Subscription[] = list.data ?? [];

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Money</p>
        <h1 className="mt-2 text-3xl font-semibold">Подписки</h1>
        <p className="mt-1 text-sm text-gray-400">
          Трекер регулярных платежей. Telegram-уведомление приходит за{' '}
          <span className="text-gray-300">N дней</span> до даты оплаты
          (по умолчанию — за 1 день).
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <Stat
          title="Активных"
          value={summary.data?.active_count ?? 0}
          hint={`всего ${summary.data?.total_count ?? 0}`}
          accent="accent"
        />
        <Stat
          title="В месяц"
          value={Math.round(summary.data?.monthly_total ?? 0)}
          hint="нормализовано к месяцу"
          accent="warning"
        />
        <Stat
          title="Скоро · 7 дней"
          value={summary.data?.upcoming.length ?? 0}
          accent={(summary.data?.upcoming.length ?? 0) > 0 ? 'danger' : 'success'}
        />
      </section>

      <NewSubscriptionForm />

      <Card>
        <CardHeader title="Все подписки" hint={`${items.length} записей`} />
        <div className="space-y-2 px-5 pb-5 pt-3">
          {list.isLoading && <div className="text-sm text-gray-500">Загрузка…</div>}
          {!list.isLoading && items.length === 0 && (
            <div className="rounded-xl border border-dashed border-border px-4 py-10 text-center text-sm text-gray-500">
              Пока пусто. Добавьте первую подписку выше.
            </div>
          )}
          <AnimatePresence>
            {items.map((s) => {
              const due = daysUntil(s.next_billing_date);
              const tone =
                due < 0
                  ? 'text-danger'
                  : due <= 1
                    ? 'text-warning'
                    : due <= 7
                      ? 'text-accent-glow'
                      : 'text-gray-400';
              return (
                <motion.div
                  key={s.id}
                  layout
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={cn(
                    'group flex items-center gap-3 rounded-xl border border-border bg-bg-card/60 px-4 py-3 transition hover:border-border-strong',
                    !s.active && 'opacity-50',
                  )}
                >
                  <div className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-bg-subtle text-gray-400">
                    <Wallet size={16} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{s.name}</div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-3 text-[11px] text-gray-500">
                      <span>{formatMoney(Number(s.amount), s.currency)}</span>
                      <span>·</span>
                      <span>{s.billing_period}</span>
                      {s.notify_days_before !== 1 && (
                        <>
                          <span>·</span>
                          <span>напомнить за {s.notify_days_before} дн.</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className={cn('flex shrink-0 items-center gap-1.5 text-xs', tone)}>
                    <CalendarClock size={13} />
                    <span suppressHydrationWarning>
                      {due < 0
                        ? `${-due}д назад`
                        : due === 0
                          ? 'сегодня'
                          : `через ${due}д`}
                    </span>
                  </div>
                  <button
                    onClick={() => remove.mutate(s.id)}
                    className="text-gray-500 opacity-0 transition hover:text-danger group-hover:opacity-100"
                    aria-label="delete"
                  >
                    <X size={14} />
                  </button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </Card>
    </div>
  );
}

function NewSubscriptionForm() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [period, setPeriod] = useState<BillingPeriod>('monthly');
  const [nextDate, setNextDate] = useState('');
  const [notify, setNotify] = useState(1);

  const create = useMutation({
    mutationFn: () =>
      subscriptionsApi.create({
        name,
        amount: Number(amount) || 0,
        currency,
        billing_period: period,
        next_billing_date: nextDate,
        notify_days_before: notify,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['subscriptions'] });
      setName('');
      setAmount('');
      setOpen(false);
    },
  });

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-sm text-accent-glow transition hover:border-accent"
      >
        <Plus size={14} /> Добавить подписку
      </button>
    );
  }

  return (
    <Card className="px-5 py-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim() && nextDate) create.mutate();
        }}
        className="grid grid-cols-1 gap-3 md:grid-cols-2"
      >
        <Field label="Название" hint="например, Netflix">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          />
        </Field>
        <Field label="Сумма" hint="число">
          <div className="flex gap-2">
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              type="number"
              step="0.01"
              min="0"
              required
              className="flex-1 rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
            />
            <input
              value={currency}
              onChange={(e) => setCurrency(e.target.value.toUpperCase().slice(0, 4))}
              className="w-20 rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
            />
          </div>
        </Field>
        <Field label="Период">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as BillingPeriod)}
            className="w-full rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          >
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Дата следующего списания">
          <input
            type="date"
            value={nextDate}
            onChange={(e) => setNextDate(e.target.value)}
            required
            className="w-full rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          />
        </Field>
        <Field label="Напомнить за (дней)">
          <input
            type="number"
            min={0}
            max={30}
            value={notify}
            onChange={(e) => setNotify(Math.max(0, Math.min(30, Number(e.target.value) || 0)))}
            className="w-full rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          />
        </Field>
        <div className="flex items-end justify-end gap-2">
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="rounded-md border border-border bg-bg-card/60 px-3 py-2 text-xs text-gray-300 hover:text-gray-100"
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={create.isPending || !name.trim() || !nextDate}
            className="rounded-md border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow disabled:opacity-50"
          >
            Сохранить
          </button>
        </div>
      </form>
    </Card>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] uppercase tracking-wider text-gray-500">{label}</span>
      {children}
      {hint && <span className="text-[10px] text-gray-600">{hint}</span>}
    </label>
  );
}

import { StatusBadge } from '@/components/StatusBadge';

const phases = [
  { id: 0, name: 'Bootstrap', status: 'done' },
  { id: 1, name: 'Core task manager', status: 'next' },
  { id: 2, name: 'Notes ingestion', status: 'todo' },
  { id: 3, name: 'AI extraction', status: 'todo' },
  { id: 4, name: 'Scheduling', status: 'todo' },
  { id: 5, name: 'Notifications', status: 'todo' },
  { id: 6, name: 'Learning planner', status: 'todo' },
  { id: 7, name: 'Anti-procrastination', status: 'todo' },
  { id: 8, name: 'Polish', status: 'todo' },
] as const;

const statusStyles: Record<string, string> = {
  done: 'border-success/40 bg-success/10 text-success',
  next: 'border-accent/40 bg-accent/10 text-accent-glow',
  todo: 'border-border bg-bg-subtle text-gray-400',
};

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <header className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">NeuroPlan</p>
          <h1 className="mt-3 text-5xl font-semibold leading-tight tracking-tight">
            AI productivity dashboard
          </h1>
          <p className="mt-4 max-w-xl text-gray-400">
            Личный исполнительный ассистент: задачи, заметки, обучение и напоминания —
            в одном месте, с AI-приоритизацией и борьбой с прокрастинацией.
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <StatusBadge url="/api/backend/api/v1/health" label="API" />
          <StatusBadge url="/api/backend/api/v1/health/db" label="Database" />
        </div>
      </header>

      <section className="mt-14 grid gap-4 md:grid-cols-3">
        <Card title="Tasks" value="—" hint="Phase 1" />
        <Card title="Focus score" value="—" hint="Phase 7" />
        <Card title="Learning" value="—" hint="Phase 6" />
      </section>

      <section className="mt-14">
        <h2 className="text-sm font-medium uppercase tracking-wider text-gray-500">
          Roadmap
        </h2>
        <ol className="mt-4 grid gap-2 md:grid-cols-2">
          {phases.map((p) => (
            <li
              key={p.id}
              className="flex items-center justify-between rounded-xl border border-border bg-bg-card/60 px-4 py-3 shadow-card backdrop-blur"
            >
              <div className="flex items-center gap-3">
                <span className="rounded-md bg-bg-subtle px-2 py-0.5 font-mono text-xs text-gray-400">
                  P{p.id}
                </span>
                <span className="text-sm">{p.name}</span>
              </div>
              <span
                className={
                  'rounded-full border px-2.5 py-0.5 text-[10px] uppercase tracking-wider ' +
                  statusStyles[p.status]
                }
              >
                {p.status}
              </span>
            </li>
          ))}
        </ol>
      </section>

      <footer className="mt-16 text-xs text-gray-500">
        Phase 0 bootstrap · web · api · worker · postgres · redis are running in docker compose.
      </footer>
    </main>
  );
}

function Card({ title, value, hint }: { title: string; value: string; hint: string }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border bg-bg-card p-5 shadow-card transition hover:border-border-strong hover:shadow-glow">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-gray-500">{title}</span>
        <span className="text-[10px] text-gray-600">{hint}</span>
      </div>
      <div className="mt-6 text-4xl font-semibold text-gray-100">{value}</div>
    </div>
  );
}

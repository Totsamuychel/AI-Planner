'use client';

import { Bell, Search } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';

export function Topbar() {
  return (
    <div className="sticky top-0 z-20 flex items-center gap-3 border-b border-border bg-bg/80 px-6 py-3 backdrop-blur">
      <button
        type="button"
        onClick={() => window.dispatchEvent(new Event('open-command-palette'))}
        className="group relative flex flex-1 max-w-md items-center rounded-lg border border-border bg-bg-card/60 py-2 pl-9 pr-3 text-left text-sm text-gray-500 transition hover:border-accent/60"
      >
        <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <span className="flex-1">Поиск задач, заметок, команд…</span>
        <kbd className="rounded border border-border bg-bg-subtle px-1.5 py-0.5 font-mono text-[10px] text-gray-500">
          ⌘K
        </kbd>
      </button>
      <StatusBadge url="/api/backend/api/v1/health" label="API" />
      <StatusBadge url="/api/backend/api/v1/health/db" label="DB" />
      <button
        className="rounded-lg border border-border bg-bg-card/60 p-2 text-gray-400 hover:text-gray-100"
        aria-label="Notifications"
      >
        <Bell size={14} />
      </button>
    </div>
  );
}

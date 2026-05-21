'use client';

import { Bell, Search } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';

export function Topbar() {
  return (
    <div className="sticky top-0 z-20 flex items-center gap-3 border-b border-border bg-bg/80 px-6 py-3 backdrop-blur">
      <div className="relative flex-1 max-w-md">
        <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          placeholder="Search tasks, notes…  (⌘K coming in Phase 8)"
          className="w-full rounded-lg border border-border bg-bg-card/60 py-2 pl-9 pr-3 text-sm placeholder:text-gray-500 focus:border-accent/60 focus:outline-none"
        />
      </div>
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

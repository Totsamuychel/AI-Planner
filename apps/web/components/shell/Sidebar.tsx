'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  CalendarDays,
  GraduationCap,
  Inbox,
  LayoutDashboard,
  LineChart,
  ListChecks,
  Settings,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/cn';

type Item = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string; size?: number }>;
  phase?: number;
  enabled?: boolean;
};

const items: Item[] = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard, enabled: true },
  { href: '/tasks', label: 'Tasks', icon: ListChecks, enabled: true },
  { href: '/calendar', label: 'Calendar', icon: CalendarDays, enabled: true },
  { href: '/inbox', label: 'Notes Inbox', icon: Inbox, enabled: true },
  { href: '/learning', label: 'Learning', icon: GraduationCap, enabled: true },
  { href: '/analytics', label: 'Analytics', icon: LineChart, phase: 8 },
  { href: '/settings', label: 'Settings', icon: Settings, enabled: true },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 border-r border-border bg-bg-subtle/60 px-4 py-6 backdrop-blur md:flex md:flex-col">
      <Link href="/" className="mb-8 flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-accent to-accent-glow shadow-glow">
          <Sparkles size={16} className="text-bg" />
        </span>
        <div className="leading-tight">
          <div className="text-sm font-semibold">NeuroPlan</div>
          <div className="text-[10px] uppercase tracking-widest text-gray-500">v0.1</div>
        </div>
      </Link>

      <nav className="flex flex-col gap-1">
        {items.map((it) => {
          const active = pathname === it.href || (it.href !== '/' && pathname.startsWith(it.href));
          const disabled = !it.enabled;
          const Icon = it.icon;
          const cls = cn(
            'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition',
            active
              ? 'bg-bg-card text-white shadow-card'
              : 'text-gray-400 hover:bg-bg-card/60 hover:text-gray-100',
            disabled && 'pointer-events-none opacity-40',
          );
          return (
            <Link href={it.href} key={it.href} className={cls}>
              <Icon size={16} className={active ? 'text-accent-glow' : ''} />
              <span className="flex-1">{it.label}</span>
              {it.phase && (
                <span className="rounded bg-bg-subtle px-1.5 py-0.5 font-mono text-[10px] text-gray-500">
                  P{it.phase}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-xl border border-border bg-bg-card/60 p-3 text-xs text-gray-400">
        <p className="text-[10px] uppercase tracking-widest text-gray-500">Phase 6 active</p>
        <p className="mt-2 leading-relaxed">
          Learning Planner — goals, sessions, and spaced repetition.
        </p>
      </div>
    </aside>
  );
}

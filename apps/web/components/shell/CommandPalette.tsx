'use client';

import { useQueryClient } from '@tanstack/react-query';
import {
  BarChart3,
  CalendarDays,
  CheckSquare,
  Grid2x2,
  GraduationCap,
  Inbox,
  LayoutDashboard,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  Target,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { notesApi, scheduleApi, tasksApi, type Task } from '@/lib/api';
import { cn } from '@/lib/cn';

interface Command {
  id: string;
  label: string;
  hint?: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  run: () => void | Promise<void>;
}

export function CommandPalette() {
  const router = useRouter();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const [taskResults, setTaskResults] = useState<Task[]>([]);

  const close = useCallback(() => {
    setOpen(false);
    setQuery('');
    setActive(0);
    setTaskResults([]);
  }, []);

  // Global ⌘K / Ctrl+K toggle + custom open event (fired by the Topbar search).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    const onOpen = () => setOpen(true);
    window.addEventListener('keydown', onKey);
    window.addEventListener('open-command-palette', onOpen);
    return () => {
      window.removeEventListener('keydown', onKey);
      window.removeEventListener('open-command-palette', onOpen);
    };
  }, []);

  const commands = useMemo<Command[]>(() => {
    const go = (href: string) => () => {
      router.push(href as never);
      close();
    };
    return [
      { id: 'nav-dashboard', label: 'Go to Dashboard', icon: LayoutDashboard, run: go('/') },
      { id: 'nav-tasks', label: 'Go to Tasks', icon: CheckSquare, run: go('/tasks') },
      { id: 'nav-matrix', label: 'Go to Eisenhower matrix', icon: Grid2x2, run: go('/matrix') },
      { id: 'nav-calendar', label: 'Go to Calendar', icon: CalendarDays, run: go('/calendar') },
      { id: 'nav-inbox', label: 'Go to Notes Inbox', icon: Inbox, run: go('/inbox') },
      { id: 'nav-learning', label: 'Go to Learning', icon: GraduationCap, run: go('/learning') },
      { id: 'nav-focus', label: 'Go to Focus Mode', icon: Sparkles, run: go('/focus') },
      { id: 'nav-analytics', label: 'Go to Analytics', icon: BarChart3, run: go('/analytics') },
      { id: 'nav-settings', label: 'Go to Settings', icon: Settings, run: go('/settings') },
      {
        id: 'act-sync',
        label: 'Sync Obsidian vault',
        hint: 'action',
        icon: RefreshCw,
        run: async () => {
          close();
          await notesApi.syncAll().catch(() => {});
          qc.invalidateQueries({ queryKey: ['notes'] });
          router.push('/inbox' as never);
        },
      },
      {
        id: 'act-plan',
        label: 'Generate day plan',
        hint: 'action',
        icon: CalendarDays,
        run: async () => {
          close();
          await scheduleApi.generate().catch(() => {});
          qc.invalidateQueries({ queryKey: ['schedule'] });
          qc.invalidateQueries({ queryKey: ['tasks'] });
          router.push('/calendar' as never);
        },
      },
      {
        id: 'act-aisort',
        label: 'AI-sort the Eisenhower matrix',
        hint: 'action',
        icon: Target,
        run: async () => {
          close();
          await tasksApi.aiSortMatrix().catch(() => {});
          qc.invalidateQueries({ queryKey: ['tasks'] });
          router.push('/matrix' as never);
        },
      },
    ];
  }, [router, qc, close]);

  const filteredCommands = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) => c.label.toLowerCase().includes(q));
  }, [commands, query]);

  // Debounced task search.
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setTaskResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ search: q, limit: '6' });
        const page = await tasksApi.list(params);
        setTaskResults(page.items);
      } catch {
        setTaskResults([]);
      }
    }, 220);
    return () => clearTimeout(t);
  }, [query]);

  type Row =
    | { kind: 'command'; cmd: Command }
    | { kind: 'task'; task: Task };

  const rows: Row[] = useMemo(
    () => [
      ...filteredCommands.map((cmd) => ({ kind: 'command' as const, cmd })),
      ...taskResults.map((task) => ({ kind: 'task' as const, task })),
    ],
    [filteredCommands, taskResults],
  );

  useEffect(() => {
    setActive((a) => Math.min(a, Math.max(0, rows.length - 1)));
  }, [rows.length]);

  const runRow = useCallback(
    (row: Row) => {
      if (row.kind === 'command') {
        void row.cmd.run();
      } else {
        router.push('/tasks' as never);
        close();
      }
    },
    [router, close],
  );

  const onListKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, rows.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === 'Enter' && rows[active]) {
      e.preventDefault();
      runRow(rows[active]);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[12vh]"
      onClick={close}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-border-strong bg-bg-card shadow-glow"
      >
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Search size={16} className="text-gray-500" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onListKey}
            placeholder="Поиск команд и задач…"
            className="flex-1 bg-transparent text-sm placeholder:text-gray-500 focus:outline-none"
          />
          <kbd className="rounded border border-border bg-bg-subtle px-1.5 py-0.5 text-[10px] text-gray-500">
            ESC
          </kbd>
        </div>

        <div className="max-h-[55vh] overflow-y-auto py-2">
          {rows.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-gray-500">Ничего не найдено</div>
          )}

          {filteredCommands.length > 0 && (
            <Section label="Команды" />
          )}
          {rows.map((row, i) => {
            if (row.kind === 'task' && i > 0 && rows[i - 1].kind === 'command') {
              return (
                <div key="task-sep">
                  <Section label="Задачи" />
                  <RowItem
                    row={row}
                    activeRow={i === active}
                    onClick={() => runRow(row)}
                    onHover={() => setActive(i)}
                  />
                </div>
              );
            }
            return (
              <RowItem
                key={row.kind === 'command' ? row.cmd.id : row.task.id}
                row={row}
                activeRow={i === active}
                onClick={() => runRow(row)}
                onHover={() => setActive(i)}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Section({ label }: { label: string }) {
  return (
    <div className="px-4 pb-1 pt-2 text-[10px] uppercase tracking-widest text-gray-600">
      {label}
    </div>
  );
}

function RowItem({
  row,
  activeRow,
  onClick,
  onHover,
}: {
  row:
    | { kind: 'command'; cmd: Command }
    | { kind: 'task'; task: Task };
  activeRow: boolean;
  onClick: () => void;
  onHover: () => void;
}) {
  const Icon = row.kind === 'command' ? row.cmd.icon : CheckSquare;
  const label = row.kind === 'command' ? row.cmd.label : row.task.title;
  const hint = row.kind === 'command' ? row.cmd.hint : row.task.priority;
  return (
    <button
      onClick={onClick}
      onMouseEnter={onHover}
      className={cn(
        'flex w-full items-center gap-3 px-4 py-2 text-left text-sm transition',
        activeRow ? 'bg-accent/15 text-white' : 'text-gray-300 hover:bg-bg-subtle/60',
      )}
    >
      <Icon size={15} className={activeRow ? 'text-accent-glow' : 'text-gray-500'} />
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {hint && (
        <span className="shrink-0 rounded border border-border bg-bg-subtle px-1.5 py-0.5 font-mono text-[10px] text-gray-500">
          {hint}
        </span>
      )}
    </button>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/cn';

type State = 'checking' | 'ok' | 'fail';

export function StatusBadge({ url, label }: { url: string; label: string }) {
  const [state, setState] = useState<State>('checking');

  useEffect(() => {
    let alive = true;
    const ping = async () => {
      try {
        const r = await fetch(url, { cache: 'no-store' });
        if (!alive) return;
        setState(r.ok ? 'ok' : 'fail');
      } catch {
        if (alive) setState('fail');
      }
    };
    ping();
    const id = setInterval(ping, 10_000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [url]);

  const dot =
    state === 'ok'
      ? 'bg-success shadow-[0_0_10px_rgba(52,211,153,0.7)]'
      : state === 'fail'
        ? 'bg-danger shadow-[0_0_10px_rgba(251,113,133,0.7)]'
        : 'bg-warning';

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-border bg-bg-card/60 px-3 py-1.5 text-xs text-gray-300 backdrop-blur">
      <span className={cn('h-2 w-2 rounded-full', dot)} />
      <span className="font-medium">{label}</span>
      <span className="text-gray-500">·</span>
      <span className="text-gray-400">
        {state === 'ok' ? 'online' : state === 'fail' ? 'unreachable' : 'checking…'}
      </span>
    </div>
  );
}

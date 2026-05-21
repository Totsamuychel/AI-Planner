import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';

export function Card({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-border bg-bg-card shadow-card backdrop-blur transition hover:border-border-strong',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  hint,
  right,
}: {
  title: string;
  hint?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between px-5 pt-5">
      <div>
        <div className="text-xs uppercase tracking-wider text-gray-500">{title}</div>
        {hint && <div className="mt-0.5 text-[11px] text-gray-600">{hint}</div>}
      </div>
      {right}
    </div>
  );
}

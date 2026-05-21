'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { useState } from 'react';
import { tasksApi } from '@/lib/api';

export function NewTaskForm() {
  const [title, setTitle] = useState('');
  const qc = useQueryClient();
  const mut = useMutation({
    mutationFn: (t: string) => tasksApi.create({ title: t }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] });
      qc.invalidateQueries({ queryKey: ['analytics'] });
      setTitle('');
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const t = title.trim();
        if (t) mut.mutate(t);
      }}
      className="flex items-center gap-2 rounded-xl border border-border bg-bg-card/60 px-3 py-2 focus-within:border-accent/60"
    >
      <Plus size={14} className="text-gray-500" />
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Add a task… (press Enter)"
        className="flex-1 bg-transparent text-sm placeholder:text-gray-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={!title.trim() || mut.isPending}
        className="rounded-md border border-accent/40 bg-accent/10 px-3 py-1 text-xs text-accent-glow disabled:opacity-30"
      >
        Add
      </button>
    </form>
  );
}

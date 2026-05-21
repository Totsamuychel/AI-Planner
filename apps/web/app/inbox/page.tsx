'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, FileText, RefreshCw, X } from 'lucide-react';
import { useState } from 'react';
import { notesApi, type EntityType, type InboxEntity, type NoteSourceType } from '@/lib/api';
import { cn } from '@/lib/cn';
import { Card, CardHeader } from '@/components/ui/Card';

const ENTITY_TYPES: { id: EntityType | 'all'; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'task', label: 'Tasks' },
  { id: 'event', label: 'Events' },
  { id: 'learning', label: 'Learning' },
  { id: 'idea', label: 'Ideas' },
];

export default function InboxPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<EntityType | 'all'>('all');

  const sources = useQuery({ queryKey: ['notes', 'sources'], queryFn: notesApi.listSources });
  const aiStatus = useQuery({ queryKey: ['notes', 'ai-status'], queryFn: notesApi.aiStatus });
  const inbox = useQuery({
    queryKey: ['notes', 'inbox', filter],
    queryFn: () => {
      const p = new URLSearchParams();
      if (filter !== 'all') p.append('entity_type', filter);
      p.set('limit', '100');
      return notesApi.inbox(p);
    },
  });

  const syncAll = useMutation({
    mutationFn: notesApi.syncAll,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notes'] });
    },
  });

  const accept = useMutation({
    mutationFn: (id: string) => notesApi.accept(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['notes', 'inbox'] });
      qc.setQueryData<{ items: InboxEntity[]; total: number }>(
        ['notes', 'inbox', filter],
        (prev) =>
          prev ? { ...prev, items: prev.items.filter((e) => e.id !== id) } : prev,
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] });
      qc.invalidateQueries({ queryKey: ['analytics'] });
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['notes', 'inbox'] }),
  });

  const reject = useMutation({
    mutationFn: (id: string) => notesApi.reject(id),
    onMutate: async (id) => {
      qc.setQueryData<{ items: InboxEntity[]; total: number }>(
        ['notes', 'inbox', filter],
        (prev) =>
          prev ? { ...prev, items: prev.items.filter((e) => e.id !== id) } : prev,
      );
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['notes', 'inbox'] }),
  });

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-accent-glow">Notes</p>
          <h1 className="mt-2 text-3xl font-semibold">Inbox</h1>
          <p className="mt-1 text-sm text-gray-400">
            {inbox.data?.total ?? 0} pending items extracted from your notes vault.
          </p>
          {aiStatus.data && (
            <p className="mt-2 inline-flex items-center gap-2 rounded-full border border-border bg-bg-card/60 px-3 py-1 text-[11px] text-gray-300">
              <span
                className={cn(
                  'h-1.5 w-1.5 rounded-full',
                  aiStatus.data.enabled ? 'bg-success' : 'bg-warning',
                )}
              />
              {aiStatus.data.enabled
                ? `AI extraction: ${aiStatus.data.provider}`
                : 'AI extraction: heuristic only (set OPENAI_API_KEY to enable)'}
            </p>
          )}
        </div>
        <button
          onClick={() => syncAll.mutate()}
          disabled={syncAll.isPending}
          className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow transition hover:border-accent disabled:opacity-50"
        >
          <RefreshCw size={14} className={syncAll.isPending ? 'animate-spin' : ''} />
          Sync vault now
        </button>
      </header>

      <SourcesCard sources={sources.data ?? []} />

      <div className="flex flex-wrap items-center gap-2">
        {ENTITY_TYPES.map((t) => (
          <button
            key={t.id}
            onClick={() => setFilter(t.id)}
            className={cn(
              'rounded-full border px-3 py-1 text-xs transition',
              filter === t.id
                ? 'border-accent/60 bg-accent/15 text-accent-glow'
                : 'border-border bg-bg-card/60 text-gray-400 hover:text-gray-100',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        <AnimatePresence>
          {inbox.data?.items.map((ent) => (
            <EntityCard
              key={ent.id}
              entity={ent}
              onAccept={() => accept.mutate(ent.id)}
              onReject={() => reject.mutate(ent.id)}
            />
          ))}
        </AnimatePresence>
        {!inbox.isLoading && (inbox.data?.items.length ?? 0) === 0 && (
          <Card>
            <div className="px-5 py-10 text-center text-sm text-gray-500">
              Inbox пуст. Добавьте источник заметок и нажмите «Sync vault now».
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

function SourcesCard({ sources }: { sources: { id: string; name: string; path: string; last_synced_at: string | null; last_error: string | null }[] }) {
  const qc = useQueryClient();
  const [name, setName] = useState('');
  const [path, setPath] = useState('/data/vault');
  const [type, setType] = useState<NoteSourceType>('obsidian');

  const add = useMutation({
    mutationFn: () => notesApi.createSource({ name, path, type }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notes', 'sources'] });
      setName('');
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => notesApi.deleteSource(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notes', 'sources'] }),
  });

  return (
    <Card>
      <CardHeader title="Sources" hint="Folders that AI Planner scans for markdown notes" />
      <div className="space-y-3 px-5 pb-5 pt-3">
        {sources.length === 0 && (
          <div className="rounded-lg border border-dashed border-border px-3 py-4 text-xs text-gray-500">
            No sources yet — точка монтирования `/data/vault` уже подключена в Docker.
            Скопируйте туда свои Obsidian-заметки и добавьте источник ниже.
          </div>
        )}
        {sources.map((s) => (
          <div
            key={s.id}
            className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-bg-card/60 px-3 py-2 text-sm"
          >
            <FileText size={14} className="text-accent-glow" />
            <span className="font-medium">{s.name}</span>
            <span className="text-xs text-gray-500">{s.path}</span>
            <span className="ml-auto text-[11px] text-gray-500">
              {s.last_synced_at ? `synced ${new Date(s.last_synced_at).toLocaleTimeString()}` : 'never'}
            </span>
            <button
              onClick={() => remove.mutate(s.id)}
              className="text-gray-400 hover:text-danger"
              aria-label="remove"
            >
              <X size={14} />
            </button>
          </div>
        ))}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) add.mutate();
          }}
          className="grid grid-cols-1 gap-2 md:grid-cols-[1fr,2fr,auto,auto]"
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name (My Vault)"
            className="rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          />
          <input
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/data/vault"
            className="rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value as NoteSourceType)}
            className="rounded-md border border-border bg-bg-card/60 px-3 py-2 text-sm focus:border-accent/60 focus:outline-none"
          >
            <option value="obsidian">obsidian</option>
            <option value="markdown_dir">markdown_dir</option>
            <option value="txt_dir">txt_dir</option>
          </select>
          <button
            type="submit"
            disabled={add.isPending || !name.trim()}
            className="rounded-md border border-accent/40 bg-accent/10 px-3 py-2 text-xs text-accent-glow disabled:opacity-40"
          >
            Add source
          </button>
        </form>
      </div>
    </Card>
  );
}

const TYPE_COLORS: Record<string, string> = {
  task: 'border-accent/40 bg-accent/10 text-accent-glow',
  event: 'border-info/40 bg-info/10 text-info',
  learning: 'border-success/40 bg-success/10 text-success',
  idea: 'border-warning/40 bg-warning/10 text-warning',
  reference: 'border-border bg-bg-subtle text-gray-400',
  info: 'border-border bg-bg-subtle text-gray-400',
  reflection: 'border-border bg-bg-subtle text-gray-400',
};

function EntityCard({
  entity,
  onAccept,
  onReject,
}: {
  entity: InboxEntity;
  onAccept: () => void;
  onReject: () => void;
}) {
  const due = (entity.normalized_data?.due_at as string | undefined) ?? null;
  const aiMeta = entity.normalized_data?.ai_meta as { ai?: boolean } | undefined;
  const aiTouched = !!aiMeta?.ai;
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <Card className="px-5 py-4">
        <div className="flex flex-wrap items-start gap-3">
          <span
            className={cn(
              'rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider',
              TYPE_COLORS[entity.entity_type],
            )}
          >
            {entity.entity_type}
          </span>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium">{entity.title}</div>
            {entity.source_excerpt && (
              <div className="mt-1 line-clamp-2 text-xs italic text-gray-500">
                “{entity.source_excerpt}”
              </div>
            )}
            <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-gray-500">
              <span>confidence {Math.round(entity.confidence * 100)}%</span>
              {due && <span>due {new Date(due).toLocaleString()}</span>}
              {entity.source_line && <span>line {entity.source_line}</span>}
              {aiTouched && (
                <span className="rounded-full border border-accent/40 bg-accent/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-accent-glow">
                  AI
                </span>
              )}
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <button
              onClick={onReject}
              title="Reject"
              className="rounded-md border border-border bg-bg-card/60 p-2 text-gray-400 transition hover:border-danger/60 hover:text-danger"
            >
              <X size={14} />
            </button>
            <button
              onClick={onAccept}
              title="Promote to task"
              className="rounded-md border border-success/40 bg-success/10 p-2 text-success transition hover:border-success"
            >
              <Check size={14} />
            </button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

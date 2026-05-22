// Browser → Next rewrite → FastAPI
export const API_BASE = '/api/backend';

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API ${status}`);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
    ...init,
  });
  if (!r.ok) {
    let body: unknown = null;
    try {
      body = await r.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(r.status, body);
  }
  if (r.status === 204) return undefined as T;
  return (await r.json()) as T;
}

// ---------- domain types (mirrors backend Pydantic) ----------

export type TaskStatus = 'inbox' | 'planned' | 'active' | 'done' | 'archived' | 'snoozed';
export type PriorityBucket = 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
export type EnergyType = 'deep' | 'shallow' | 'errand' | 'learning' | 'social';

export interface Task {
  id: string;
  owner_id: string;
  project_id: string | null;
  parent_id: string | null;
  title: string;
  description: string;
  status: TaskStatus;
  priority: PriorityBucket;
  energy_type: EnergyType | null;
  priority_score: number;
  urgency_score: number;
  importance_score: number;
  effort_score: number;
  procrastination_score: number;
  snooze_count: number;
  due_date: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  completed_at: string | null;
  snoozed_until: string | null;
  estimated_minutes: number | null;
  actual_minutes: number | null;
  tags: { id: string; name: string; color: string }[];
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Project {
  id: string;
  name: string;
  color: string;
  description: string;
  archived: boolean;
}

export interface DashboardAnalytics {
  totals: {
    all: number;
    open: number;
    overdue: number;
    completed_today: number;
    completed_7d: number;
  };
  completion_7d: { day: string; count: number }[];
  as_of: string;
}

// ---------- endpoints ----------

export const tasksApi = {
  list: (params?: URLSearchParams) =>
    api<Page<Task>>(`/api/v1/tasks${params?.toString() ? `?${params}` : ''}`),
  create: (body: Partial<Task> & { title: string }) =>
    api<Task>('/api/v1/tasks', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: Partial<Task>) =>
    api<Task>(`/api/v1/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  complete: (id: string) => api<Task>(`/api/v1/tasks/${id}/complete`, { method: 'POST' }),
  remove: (id: string) => api<void>(`/api/v1/tasks/${id}`, { method: 'DELETE' }),
  decompose: (id: string) => api<Task[]>(`/api/v1/tasks/${id}/decompose`, { method: 'POST' }),
  setScores: (id: string, body: { importance_score: number; urgency_score: number }) =>
    api<Task>(`/api/v1/tasks/${id}/scores`, { method: 'PATCH', body: JSON.stringify(body) }),
  aiSortMatrix: () =>
    api<{ updated: number; used_ai: boolean }>('/api/v1/tasks/eisenhower/ai-sort', {
      method: 'POST',
    }),
  reprioritize: () =>
    api<{ reprioritized: number }>('/api/v1/tasks/reprioritize', { method: 'POST' }),
};

export const projectsApi = {
  list: () => api<Project[]>('/api/v1/projects'),
  create: (body: { name: string; color?: string; description?: string }) =>
    api<Project>('/api/v1/projects', { method: 'POST', body: JSON.stringify(body) }),
};

export const analyticsApi = {
  dashboard: () => api<DashboardAnalytics>('/api/v1/analytics/dashboard'),
};

// ---------- notes ----------

export type EntityType = 'task' | 'event' | 'idea' | 'learning' | 'reference' | 'info' | 'reflection';
export type EntityStatus = 'pending' | 'accepted' | 'rejected' | 'auto';
export type NoteSourceType = 'obsidian' | 'markdown_dir' | 'txt_dir';

export interface NoteSource {
  id: string;
  name: string;
  path: string;
  type: NoteSourceType;
  enabled: boolean;
  sync_interval_seconds: number;
  last_synced_at: string | null;
  last_error: string | null;
}

export interface InboxEntity {
  id: string;
  document_id: string;
  entity_type: EntityType;
  title: string;
  content: string;
  source_excerpt: string;
  source_line: number | null;
  normalized_data: Record<string, unknown>;
  confidence: number;
  status: EntityStatus;
  promoted_task_id: string | null;
  created_at: string;
}

export interface IngestStats {
  files_seen: number;
  files_indexed: number;
  files_skipped: number;
  entities_created: number;
  errors: number;
}

export interface AIStatus {
  provider: string;
  enabled: boolean;
}

// ---------- schedule ----------

export interface ScheduledBlock {
  task_id: string;
  title: string;
  priority: PriorityBucket;
  priority_score: number;
  energy_type: EnergyType | null;
  start: string;
  end: string;
  overflow: boolean;
}

export interface DayPlan {
  date: string;
  blocks: ScheduledBlock[];
  overflow_count: number;
}

export interface WeekPlan {
  days: DayPlan[];
}

export const scheduleApi = {
  today: () => api<DayPlan>('/api/v1/schedule/today'),
  week: () => api<WeekPlan>('/api/v1/schedule/week'),
  generate: () => api<DayPlan>('/api/v1/schedule/generate', { method: 'POST' }),
  rebalance: () => api<DayPlan>('/api/v1/schedule/rebalance', { method: 'POST' }),
};

export const notesApi = {
  aiStatus: () => api<AIStatus>('/api/v1/notes/ai/status'),
  listSources: () => api<NoteSource[]>('/api/v1/notes/sources'),
  createSource: (b: { name: string; path: string; type?: NoteSourceType }) =>
    api<NoteSource>('/api/v1/notes/sources', { method: 'POST', body: JSON.stringify(b) }),
  deleteSource: (id: string) =>
    api<void>(`/api/v1/notes/sources/${id}`, { method: 'DELETE' }),
  syncAll: () =>
    api<{ sources: Record<string, IngestStats> }>('/api/v1/notes/sync', { method: 'POST' }),
  inbox: (params?: URLSearchParams) =>
    api<Page<InboxEntity>>(`/api/v1/notes/inbox${params?.toString() ? `?${params}` : ''}`),
  accept: (id: string) =>
    api<Task>(`/api/v1/notes/inbox/${id}/accept`, { method: 'POST' }),
  reject: (id: string) =>
    api<InboxEntity>(`/api/v1/notes/inbox/${id}/reject`, { method: 'POST' }),
};

// ---------- learning ----------

export type LearningItemStatus = 'backlog' | 'learning' | 'reviewing' | 'completed' | 'archived';

export interface LearningSession {
  id: string;
  learning_item_id: string;
  notes: string | null;
  duration_minutes: number;
  created_at: string;
}

export interface LearningItem {
  id: string;
  title: string;
  topic: string;
  level: string | null;
  target_date: string | null;
  status: LearningItemStatus;
  next_review_at: string | null;
  estimated_sessions: number;
  completed_sessions: number;
  sessions: LearningSession[];
}

export const learningApi = {
  listGoals: () => api<LearningItem[]>('/api/v1/learning/goals'),
  createGoal: (body: { title: string; topic: string; level?: string; estimated_sessions?: number }) =>
    api<LearningItem>('/api/v1/learning/goals', { method: 'POST', body: JSON.stringify(body) }),
  logSession: (id: string, body: { notes?: string; duration_minutes: number }) =>
    api<LearningSession>(`/api/v1/learning/goals/${id}/sessions`, { method: 'POST', body: JSON.stringify(body) }),
  getReviewItems: () => api<LearningItem[]>('/api/v1/learning/review'),
};


export const settingsApi = {
  updateTelegram: (telegram_chat_id: string | null) =>
    api<{ status: string; telegram_chat_id: string | null }>('/api/v1/settings/telegram', {
      method: 'PATCH',
      body: JSON.stringify({ telegram_chat_id }),
    }),
};

export const notificationsApi = {
  test: (message: string, channel: 'desktop' | 'telegram') =>
    api<{ status: string }>('/api/v1/notifications/test', {
      method: 'POST',
      body: JSON.stringify({ message, channel }),
    }),
};

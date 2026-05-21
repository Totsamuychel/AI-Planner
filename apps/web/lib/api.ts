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

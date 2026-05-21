// Shared cross-package TS types. Populated as backend contracts stabilize.

export type TaskStatus =
  | 'inbox'
  | 'planned'
  | 'active'
  | 'done'
  | 'archived'
  | 'snoozed';

export type PriorityBucket = 'P0' | 'P1' | 'P2' | 'P3' | 'P4';

export interface HealthResponse {
  status: 'ok' | 'fail';
  service?: string;
}

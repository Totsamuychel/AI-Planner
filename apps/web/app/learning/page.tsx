'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { learningApi, type LearningItem } from '@/lib/api';
import { GraduationCap, Target, Clock, Plus, BookOpen } from 'lucide-react';
import { cn } from '@/lib/cn';

export default function LearningPage() {
  const queryClient = useQueryClient();
  const [newTitle, setNewTitle] = useState('');
  const [newTopic, setNewTopic] = useState('');

  const { data: goals = [], isLoading } = useQuery({
    queryKey: ['learning-goals'],
    queryFn: learningApi.listGoals,
  });

  const { data: reviewItems = [] } = useQuery({
    queryKey: ['learning-reviews'],
    queryFn: learningApi.getReviewItems,
  });

  const createGoal = useMutation({
    mutationFn: () =>
      learningApi.createGoal({
        title: newTitle,
        topic: newTopic || 'General',
      }),
    onSuccess: () => {
      setNewTitle('');
      setNewTopic('');
      queryClient.invalidateQueries({ queryKey: ['learning-goals'] });
    },
  });

  const logSession = useMutation({
    mutationFn: (id: string) =>
      learningApi.logSession(id, { duration_minutes: 30 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learning-goals'] });
      queryClient.invalidateQueries({ queryKey: ['learning-reviews'] });
    },
  });

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <GraduationCap className="text-accent" />
          Learning Planner
        </h1>
      </div>

      {reviewItems.length > 0 && (
        <section className="bg-accent/10 border border-accent/20 p-6 rounded-2xl space-y-4">
          <h2 className="text-xl font-medium text-accent flex items-center gap-2">
            <Target size={20} />
            Due for Review Today
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {reviewItems.map((item) => (
              <div key={item.id} className="bg-bg-card p-4 rounded-xl border border-border shadow-sm flex flex-col gap-3">
                <div>
                  <div className="text-sm font-medium">{item.title}</div>
                  <div className="text-xs text-white/50">{item.topic}</div>
                </div>
                <button
                  onClick={() => logSession.mutate(item.id)}
                  disabled={logSession.isPending}
                  className="bg-accent text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors w-full"
                >
                  Log Review Session (30m)
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-4">
          <h2 className="text-xl font-medium">Active Goals</h2>
          {isLoading ? (
            <div className="animate-pulse bg-white/5 h-32 rounded-2xl"></div>
          ) : goals.length === 0 ? (
            <div className="text-center py-12 bg-surface border border-white/5 rounded-2xl text-white/50">
              No learning goals yet. Create one!
            </div>
          ) : (
            <div className="grid gap-4">
              {goals.map((item) => (
                <div key={item.id} className="bg-surface p-5 rounded-2xl border border-white/5 flex gap-4 items-center">
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center shrink-0",
                    item.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-accent/20 text-accent'
                  )}>
                    <BookOpen size={20} />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{item.title}</div>
                    <div className="flex gap-3 text-xs text-white/50 mt-1">
                      <span className="flex items-center gap-1"><Target size={12} /> {item.topic}</span>
                      <span className="flex items-center gap-1"><Clock size={12} /> {item.completed_sessions} / {item.estimated_sessions} sessions</span>
                      {item.next_review_at && (
                        <span>Next review: {new Date(item.next_review_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  {item.status !== 'completed' && (
                    <button
                      onClick={() => logSession.mutate(item.id)}
                      disabled={logSession.isPending}
                      className="bg-white/5 hover:bg-white/10 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                    >
                      Log Session
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="bg-surface p-6 rounded-2xl border border-white/5 sticky top-8">
            <h3 className="font-medium mb-4 flex items-center gap-2">
              <Plus size={16} /> New Goal
            </h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createGoal.mutate();
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs text-white/50 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                  placeholder="e.g. Learn LangGraph"
                />
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1">Topic</label>
                <input
                  type="text"
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent"
                  placeholder="e.g. AI, Python"
                />
              </div>
              <button
                type="submit"
                disabled={createGoal.isPending || !newTitle}
                className="w-full bg-white text-black font-medium text-sm py-2 rounded-lg hover:bg-white/90 disabled:opacity-50"
              >
                Create Goal
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

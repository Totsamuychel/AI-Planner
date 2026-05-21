'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, Square, Check, ArrowRight } from 'lucide-react';
import { tasksApi } from '@/lib/api';
import { cn } from '@/lib/cn';

export default function FocusModePage() {
  const queryClient = useQueryClient();
  const [isActive, setIsActive] = useState(false);
  const [timeLeft, setTimeLeft] = useState(25 * 60); // 25 minutes default

  const { data: tasksData } = useQuery({
    queryKey: ['tasks', { status: ['inbox', 'planned', 'active'] }],
    queryFn: () => tasksApi.list(new URLSearchParams({ limit: '1' })),
  });

  const activeTask = tasksData?.items?.[0];

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => setTimeLeft((t) => t - 1), 1000);
    } else if (timeLeft === 0) {
      setIsActive(false);
      // Here we could trigger a desktop notification
      if (Notification.permission === 'granted') {
        new Notification('Focus Session Complete!', {
          body: 'Great job! Take a short break.',
        });
      }
    }
    return () => clearInterval(interval);
  }, [isActive, timeLeft]);

  const toggleTimer = () => {
    if (!isActive && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
    setIsActive(!isActive);
  };

  const complete = useMutation({
    mutationFn: (id: string) => tasksApi.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setIsActive(false);
      setTimeLeft(25 * 60);
    },
  });

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!activeTask) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
          <Check size={32} className="text-white/20" />
        </div>
        <h1 className="text-2xl font-semibold mb-2">You're all caught up!</h1>
        <p className="text-white/50 max-w-md">
          There are no pending tasks. Take a well-deserved break or review your learning goals.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full p-8 max-w-2xl mx-auto text-center space-y-12">
      <div className="space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">Focus Mode</h1>
        <p className="text-white/50">Single-tasking for maximum productivity.</p>
      </div>

      <div className={cn(
        "w-full max-w-md bg-surface border rounded-3xl p-8 transition-all duration-500",
        isActive ? "border-accent shadow-[0_0_40px_-10px_rgba(var(--color-accent),0.3)]" : "border-white/10"
      )}>
        <div className="text-xs font-mono uppercase tracking-widest text-accent mb-4">Current Task</div>
        <h2 className="text-2xl font-medium mb-8 leading-tight">{activeTask.title}</h2>
        
        <div className="text-7xl font-light font-mono tabular-nums mb-12 tracking-tight">
          {formatTime(timeLeft)}
        </div>

        <div className="flex items-center justify-center gap-4">
          <button
            onClick={toggleTimer}
            className={cn(
              "flex items-center gap-2 px-8 py-4 rounded-2xl font-medium transition-all active:scale-95",
              isActive 
                ? "bg-white/10 hover:bg-white/20 text-white" 
                : "bg-accent hover:bg-accent/90 text-white shadow-lg shadow-accent/25"
            )}
          >
            {isActive ? <><Square size={20} fill="currentColor" /> Pause</> : <><Play size={20} fill="currentColor" /> Start Focus</>}
          </button>
          
          <button
            onClick={() => complete.mutate(activeTask.id)}
            disabled={complete.isPending}
            className="flex items-center gap-2 px-6 py-4 rounded-2xl font-medium bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 transition-all active:scale-95"
          >
            <Check size={20} /> Done
          </button>
        </div>
      </div>
      
      {activeTask.procrastination_score > 0.3 && (
        <div className="bg-warning/10 text-warning px-6 py-4 rounded-2xl text-sm max-w-md">
          <span className="font-semibold block mb-1">Anti-procrastination Nudge</span>
          You've put this off for a while. Just commit to the next 5 minutes. You can stop after that if you want to!
        </div>
      )}
    </div>
  );
}

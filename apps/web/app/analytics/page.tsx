'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import { LineChart as LineChartIcon, Activity, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/cn';

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics-dashboard'],
    queryFn: analyticsApi.dashboard,
  });

  if (isLoading) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-8 animate-pulse">
        <div className="h-8 bg-white/5 w-48 rounded-lg mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-white/5 rounded-2xl" />
          ))}
        </div>
        <div className="h-96 bg-white/5 rounded-3xl" />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { totals, completion_7d } = data;

  // Format data for recharts
  const chartData = completion_7d.map((item) => ({
    name: format(parseISO(item.day), 'MMM d'),
    completed: item.count,
  }));

  const statCards = [
    { label: 'Total Tasks', value: totals.all, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'Completed (7d)', value: totals.completed_7d, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
    { label: 'Open Tasks', value: totals.open, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-400/10' },
    { label: 'Overdue', value: totals.overdue, icon: AlertCircle, color: 'text-rose-400', bg: 'bg-rose-400/10' },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex items-center gap-2 mb-8">
        <LineChartIcon className="text-accent" size={28} />
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => (
          <div key={i} className="bg-surface border border-white/5 p-6 rounded-2xl flex flex-col gap-4 relative overflow-hidden group">
            <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0", stat.bg, stat.color)}>
              <stat.icon size={20} />
            </div>
            <div>
              <div className="text-3xl font-semibold tracking-tight">{stat.value}</div>
              <div className="text-sm text-white/50">{stat.label}</div>
            </div>
            {/* Decorative background glow */}
            <div className={cn("absolute -bottom-6 -right-6 w-24 h-24 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity", stat.bg)} />
          </div>
        ))}
      </div>

      <div className="bg-surface border border-white/5 p-8 rounded-3xl space-y-6">
        <div>
          <h2 className="text-xl font-semibold">Task Completion Trend (Last 7 Days)</h2>
          <p className="text-sm text-white/50">Your productivity momentum over the past week.</p>
        </div>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="rgba(255,255,255,0.4)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
                dy={10}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.4)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
                dx={-10}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#18181b', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                itemStyle={{ color: '#fff' }}
              />
              <Area 
                type="monotone" 
                dataKey="completed" 
                stroke="var(--color-accent)" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorCompleted)" 
                activeDot={{ r: 6, fill: "var(--color-accent)", stroke: "#18181b", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

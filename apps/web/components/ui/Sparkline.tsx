'use client';

interface Point {
  day: string;
  count: number;
}

export function Sparkline({ data, height = 60 }: { data: Point[]; height?: number }) {
  if (data.length === 0) {
    return <div className="text-sm text-gray-500">No data yet — complete a task to start the trend.</div>;
  }
  const w = 320;
  const h = height;
  const max = Math.max(1, ...data.map((d) => d.count));
  const stepX = data.length > 1 ? w / (data.length - 1) : 0;
  const points = data
    .map((d, i) => `${i * stepX},${h - (d.count / max) * (h - 8) - 4}`)
    .join(' ');
  const area = `${points} ${w},${h} 0,${h}`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      <defs>
        <linearGradient id="spark" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#7c5cff" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#7c5cff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#spark)" />
      <polyline points={points} fill="none" stroke="#a78bfa" strokeWidth="2" />
      {data.map((d, i) => (
        <circle
          key={d.day}
          cx={i * stepX}
          cy={h - (d.count / max) * (h - 8) - 4}
          r="2.5"
          fill="#e9d5ff"
        />
      ))}
    </svg>
  );
}

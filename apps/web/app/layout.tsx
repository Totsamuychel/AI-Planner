import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'NeuroPlan — AI Planner',
  description: 'Personal productivity OS — tasks, notes, learning and reminders.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-bg text-gray-100 antialiased">
        <div className="relative min-h-screen">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[480px] bg-grid-fade"
          />
          {children}
        </div>
      </body>
    </html>
  );
}

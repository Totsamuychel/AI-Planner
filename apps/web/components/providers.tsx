'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect, type ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  useEffect(() => {
    // Connect to SSE for desktop notifications
    const eventSource = new EventSource('/api/backend/api/v1/notifications/sse');

    eventSource.onmessage = (event) => {
      if (Notification.permission === 'granted') {
        new Notification('NeuroPlan', {
          body: event.data,
          icon: '/favicon.ico',
        });
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

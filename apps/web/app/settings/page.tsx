'use client';

import { useState } from 'react';
import { settingsApi, notificationsApi } from '@/lib/api';

export default function SettingsPage() {
  const [chatId, setChatId] = useState('');
  const [testMessage, setTestMessage] = useState('Hello from AI Planner!');

  const handleSaveTelegram = async () => {
    try {
      await settingsApi.updateTelegram(chatId);
      alert('Telegram Chat ID saved successfully!');
    } catch (e) {
      alert('Failed to save Telegram Chat ID.');
      console.error(e);
    }
  };

  const handleTestDesktop = async () => {
    // Request permission if not granted
    if (Notification.permission !== 'granted') {
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') return;
    }
    try {
      await notificationsApi.test(testMessage, 'desktop');
    } catch (e) {
      console.error('Failed to send desktop test', e);
    }
  };

  const handleTestTelegram = async () => {
    try {
      await notificationsApi.test(testMessage, 'telegram');
    } catch (e) {
      console.error('Failed to send telegram test', e);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-semibold mb-6">Settings</h1>

      <section className="bg-surface p-6 rounded-2xl border border-white/5 space-y-4 shadow-sm">
        <h2 className="text-xl font-medium">Telegram Bot</h2>
        <p className="text-sm text-white/50">
          Configure your Telegram integration. You can find your Chat ID by messaging the bot and using /help or inspecting the bot API.
        </p>
        <div className="flex gap-4">
          <input
            type="text"
            className="flex-1 bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="Enter Telegram Chat ID"
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
          />
          <button
            onClick={handleSaveTelegram}
            className="bg-accent/10 text-accent hover:bg-accent/20 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Save Chat ID
          </button>
        </div>
      </section>

      <section className="bg-surface p-6 rounded-2xl border border-white/5 space-y-4 shadow-sm">
        <h2 className="text-xl font-medium">Test Notifications</h2>
        <div className="flex flex-col gap-4">
          <input
            type="text"
            className="bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="Test message..."
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
          />
          <div className="flex gap-4">
            <button
              onClick={handleTestDesktop}
              className="bg-white/5 hover:bg-white/10 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Test Desktop Push
            </button>
            <button
              onClick={handleTestTelegram}
              className="bg-white/5 hover:bg-white/10 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Test Telegram Msg
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

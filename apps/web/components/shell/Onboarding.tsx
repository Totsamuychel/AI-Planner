'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/cn';

export function Onboarding() {
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    const hasSeen = localStorage.getItem('neuroplan_onboarding');
    if (!hasSeen) {
      // Delay slightly for dramatic effect
      const t = setTimeout(() => setIsOpen(true), 1000);
      return () => clearTimeout(t);
    }
  }, []);

  const close = () => {
    setIsOpen(false);
    localStorage.setItem('neuroplan_onboarding', 'true');
  };

  // Skip rendering until mounted so the server and client output match.
  if (!mounted) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-white/10 bg-surface shadow-2xl p-8 space-y-6"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-accent-glow flex items-center justify-center mb-2 shadow-glow">
              <Sparkles size={32} className="text-white" />
            </div>
            
            <div>
              <h2 className="text-3xl font-bold tracking-tight mb-2">Welcome to AI Planner</h2>
              <p className="text-white/60 leading-relaxed">
                Your personal productivity OS is ready. AI-powered scheduling, proactive anti-procrastination, and spaced-repetition learning — all in one place.
              </p>
            </div>

            <div className="space-y-3">
              {[
                'Connect your Notes inbox to extract tasks via AI.',
                'Use Focus Mode to regain momentum when stuck.',
                'Set up Telegram notifications in Settings.'
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3 bg-white/5 px-4 py-3 rounded-xl border border-white/5">
                  <div className="w-6 h-6 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs font-bold shrink-0">
                    {i + 1}
                  </div>
                  <span className="text-sm">{feature}</span>
                </div>
              ))}
            </div>

            <button
              onClick={close}
              className="w-full flex justify-center items-center gap-2 bg-white text-black py-4 rounded-xl font-semibold hover:bg-white/90 transition-colors"
            >
              Get Started <ArrowRight size={18} />
            </button>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

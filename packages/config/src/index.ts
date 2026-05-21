export const apiBaseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const features = {
  obsidian: false, // enabled in Phase 2
  aiExtraction: false, // enabled in Phase 3
  telegram: false, // enabled in Phase 5
};

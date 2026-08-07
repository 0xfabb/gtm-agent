const STORAGE_KEY = "kol-research-feedback";

export type Verdict = "down";

interface FeedbackStore {
  [candidateKey: string]: Verdict;
}

let cache: FeedbackStore | null = null;
const listeners = new Set<() => void>();
const EMPTY: FeedbackStore = {};

export function candidateKey(platform: string, handle: string): string {
  return `${platform}|${handle.toLowerCase()}`;
}

function read(): FeedbackStore {
  if (typeof window === "undefined") return EMPTY;
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "{}");
  } catch {
    return EMPTY;
  }
}

export function getFeedbackSnapshot(): FeedbackStore {
  if (cache === null) cache = read();
  return cache;
}

export function getServerFeedbackSnapshot(): FeedbackStore {
  return EMPTY;
}

export function subscribeFeedback(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function toggleDown(platform: string, handle: string): void {
  const key = candidateKey(platform, handle);
  const next = { ...getFeedbackSnapshot() };
  if (next[key]) {
    delete next[key];
  } else {
    next[key] = "down";
  }
  cache = next;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  listeners.forEach((listener) => listener());
}

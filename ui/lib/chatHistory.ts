import type { AgentStep, RankedCandidate, StructuredQuery } from "./types";

const STORAGE_KEY = "kol-research-chats";
const MAX_CHATS = 30;
const EMPTY_CHATS: ChatSession[] = [];

export interface ChatSession {
  id: string;
  prompt: string;
  createdAt: number;
  structuredQuery: StructuredQuery | null;
  trace: Record<string, AgentStep[]>;
  shortlist: RankedCandidate[];
}

let cache: ChatSession[] | null = null;
const listeners = new Set<() => void>();

function readFromStorage(): ChatSession[] {
  if (typeof window === "undefined") return EMPTY_CHATS;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_CHATS;
    const parsed = JSON.parse(raw) as ChatSession[];
    return parsed.sort((a, b) => b.createdAt - a.createdAt);
  } catch {
    return EMPTY_CHATS;
  }
}

function commit(chats: ChatSession[]) {
  cache = chats;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
  listeners.forEach((listener) => listener());
}

export function getChatsSnapshot(): ChatSession[] {
  if (cache === null) cache = readFromStorage();
  return cache;
}

export function getServerChatsSnapshot(): ChatSession[] {
  return EMPTY_CHATS;
}

export function subscribeChats(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function saveChat(session: ChatSession): void {
  const chats = [session, ...getChatsSnapshot().filter((c) => c.id !== session.id)].slice(
    0,
    MAX_CHATS
  );
  commit(chats);
}

export function deleteChat(id: string): void {
  commit(getChatsSnapshot().filter((c) => c.id !== id));
}

export function newChatId(): string {
  return crypto.randomUUID();
}

"use client";

import { useCallback, useRef, useState } from "react";
import type {
  AgentStep,
  CostSummary,
  FilterSummary,
  RankedCandidate,
  RefilterResponse,
  RefineResponse,
  ResearchEvent,
  SeedProfile,
  StructuredQuery,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8500";

export type ResearchStatus =
  | "idle"
  | "structuring"
  | "researching"
  | "ranking"
  | "done"
  | "error"
  | "recomputing";

interface ResearchState {
  status: ResearchStatus;
  runId: string | null;
  startedAt: number | null;
  finishedAt: number | null;
  structuredQuery: StructuredQuery | null;
  seedProfile: SeedProfile | null;
  trace: Record<string, AgentStep[]>;
  shortlist: RankedCandidate[];
  cached: RankedCandidate[];
  summary: FilterSummary | null;
  cost: CostSummary | null;
  errors: { agent: string; message: string }[];
}

const initialState: ResearchState = {
  status: "idle",
  runId: null,
  startedAt: null,
  finishedAt: null,
  structuredQuery: null,
  seedProfile: null,
  trace: {},
  shortlist: [],
  cached: [],
  summary: null,
  cost: null,
  errors: [],
};

function applyEvent(state: ResearchState, event: ResearchEvent): ResearchState {
  switch (event.type) {
    case "run_started":
      return { ...state, runId: event.run_id, startedAt: Date.now() };
    case "structured_query":
      return { ...state, status: "researching", structuredQuery: event.data };
    case "seed_profile":
      return { ...state, seedProfile: event.data };
    case "agent_step": {
      const step: AgentStep = {
        agent: event.agent,
        action: event.action,
        query: event.query,
        result: event.result,
        at: Date.now(),
      };
      const existing = state.trace[event.agent] ?? [];
      return {
        ...state,
        trace: { ...state.trace, [event.agent]: [...existing, step] },
      };
    }
    case "error":
      return { ...state, errors: [...state.errors, { agent: event.agent, message: event.message }] };
    case "filtered":
      return { ...state, status: "ranking", summary: event.data };
    case "ranking_complete":
      return { ...state, status: "ranking" };
    case "done":
      return {
        ...state,
        status: "done",
        finishedAt: Date.now(),
        shortlist: event.shortlist,
        cached: event.cached ?? [],
        cost: event.cost,
      };
    default:
      return state;
  }
}

export function useResearchStream() {
  const [state, setState] = useState<ResearchState>(initialState);
  const controllerRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    setState(initialState);
  }, []);

  const start = useCallback(async (prompt: string) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setState({ ...initialState, status: "structuring" });

    try {
      const response = await fetch(`${API_URL}/api/research`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ prompt }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Research request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;
          const event = JSON.parse(line.slice("data: ".length)) as ResearchEvent;
          setState((prev) => applyEvent(prev, event));
        }
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      setState((prev) => ({
        ...prev,
        status: "error",
        errors: [...prev.errors, { agent: "connection", message: (err as Error).message }],
      }));
    }
  }, []);

  const refilter = useCallback(
    async (overrides: { follower_min?: number; follower_max?: number; max_results?: number }) => {
      const runId = state.runId;
      if (!runId) return;

      setState((prev) => ({ ...prev, status: "recomputing" }));

      const response = await fetch(`${API_URL}/api/refilter`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ run_id: runId, ...overrides }),
      });

      if (!response.ok) {
        setState((prev) => ({
          ...prev,
          status: "done",
          errors: [...prev.errors, { agent: "refilter", message: `Refilter failed: ${response.status}` }],
        }));
        return;
      }

      const data = (await response.json()) as RefilterResponse;
      setState((prev) => ({
        ...prev,
        status: "done",
        shortlist: data.shortlist,
        cached: data.cached,
        structuredQuery: prev.structuredQuery
          ? { ...prev.structuredQuery, ...overrides }
          : prev.structuredQuery,
      }));
    },
    [state.runId]
  );

  const refine = useCallback(
    async (text: string): Promise<RefineResponse | null> => {
      const runId = state.runId;
      if (!runId) return null;

      const response = await fetch(`${API_URL}/api/refine`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ run_id: runId, text }),
      });

      if (!response.ok) return null;
      return (await response.json()) as RefineResponse;
    },
    [state.runId]
  );

  return { ...state, start, reset, refilter, refine };
}

"use client";

import { useCallback, useRef, useState } from "react";
import type { AgentStep, RankedCandidate, ResearchEvent, StructuredQuery } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8500";

export type ResearchStatus =
  | "idle"
  | "structuring"
  | "researching"
  | "ranking"
  | "done"
  | "error";

interface ResearchState {
  status: ResearchStatus;
  structuredQuery: StructuredQuery | null;
  trace: Record<string, AgentStep[]>;
  shortlist: RankedCandidate[];
  errors: { agent: string; message: string }[];
}

const initialState: ResearchState = {
  status: "idle",
  structuredQuery: null,
  trace: {},
  shortlist: [],
  errors: [],
};

function applyEvent(state: ResearchState, event: ResearchEvent): ResearchState {
  switch (event.type) {
    case "structured_query":
      return { ...state, status: "researching", structuredQuery: event.data };
    case "agent_step": {
      const step: AgentStep = {
        agent: event.agent,
        action: event.action,
        query: event.action === "searching" ? event.query : undefined,
        result: event.action === "found" ? event.result : undefined,
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
    case "ranking_complete":
      return { ...state, status: "ranking", shortlist: event.data };
    case "done":
      return { ...state, status: "done", shortlist: event.shortlist };
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

  return { ...state, start, reset };
}

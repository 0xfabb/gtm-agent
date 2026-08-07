"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ArrowUp, Menu, Sparkles } from "lucide-react";

import { ChatSidebar, type RunningEntry } from "@/components/research/ChatSidebar";
import { ResearchTrace } from "@/components/research/ResearchTrace";
import { SeedProfileCard } from "@/components/research/SeedProfileCard";
import { ShortlistResults } from "@/components/research/ShortlistResults";
import { StructuredQueryChips } from "@/components/research/StructuredQueryChips";
import {
  deleteChat,
  getChatsSnapshot,
  getServerChatsSnapshot,
  newChatId,
  saveChat,
  subscribeChats,
  type ChatSession,
} from "@/lib/chatHistory";
import { useResearchStream } from "@/lib/useResearchStream";

const EXAMPLE_PROMPTS = [
  "Skincare TikTok creators, 20-80K, Gen Z audience",
  "B2B SaaS LinkedIn creators for demand-gen",
  "Fitness YouTube shorts, under 50K subs",
];

const STATUS_LABEL: Record<string, string> = {
  structuring: "Structuring your request…",
  researching: "Researching creators live…",
  ranking: "Ranking candidates…",
  error: "Something went wrong",
};

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [refineText, setRefineText] = useState("");
  const [refining, setRefining] = useState(false);
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [runningParentId, setRunningParentId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const savedRef = useRef(false);

  const chats = useSyncExternalStore(subscribeChats, getChatsSnapshot, getServerChatsSnapshot);
  const {
    status,
    runId,
    startedAt,
    finishedAt,
    structuredQuery,
    seedProfile,
    trace,
    shortlist,
    cached,
    summary,
    cost,
    errors,
    start,
    reset,
    refilter,
    refine,
  } = useResearchStream();

  const activeChat = activeChatId ? (chats.find((c) => c.id === activeChatId) ?? null) : null;
  const busy = status === "structuring" || status === "researching" || status === "ranking";
  const recomputing = status === "recomputing";
  const hasLiveRun = !activeChat && (busy || status === "done" || status === "recomputing");

  useEffect(() => {
    if (status !== "done" || savedRef.current || !submittedPrompt || !runId || !structuredQuery) {
      return;
    }
    savedRef.current = true;
    const id = newChatId();
    const session: ChatSession = {
      id,
      runId,
      parentId: runningParentId,
      prompt: submittedPrompt,
      createdAt: Date.now(),
      elapsedMs: startedAt && finishedAt ? finishedAt - startedAt : null,
      structuredQuery,
      seedProfile,
      trace,
      shortlist,
      cached,
      cost,
    };
    saveChat(session);
    setActiveChatId(id);
    setRunningParentId(null);
  }, [
    status,
    submittedPrompt,
    runId,
    structuredQuery,
    seedProfile,
    trace,
    shortlist,
    cached,
    cost,
    startedAt,
    finishedAt,
    runningParentId,
  ]);

  const displayedStructuredQuery = activeChat ? activeChat.structuredQuery : structuredQuery;
  const displayedTrace = activeChat ? activeChat.trace : trace;
  const displayedShortlist = activeChat ? activeChat.shortlist : shortlist;
  const displayedCached = activeChat ? (activeChat.cached ?? []) : cached;
  const displayedSeedProfile = activeChat ? (activeChat.seedProfile ?? null) : seedProfile;
  const displayedTitle = activeChat?.prompt ?? submittedPrompt;

  function submit(text: string, parentId: string | null = null) {
    if (!text.trim() || busy) return;
    savedRef.current = false;
    setRunningParentId(parentId);
    setSubmittedPrompt(text.trim());
    setActiveChatId(null);
    start(text.trim());
  }

  function handleNewChat() {
    reset();
    setActiveChatId(null);
    setPrompt("");
    setRefineText("");
    savedRef.current = false;
    setRunningParentId(null);
    setSidebarOpen(false);
  }

  function handleSelectChat(id: string) {
    reset();
    setActiveChatId(id);
    setRefineText("");
    setSidebarOpen(false);
  }

  function handleDeleteChat(id: string) {
    deleteChat(id);
    if (activeChatId === id) handleNewChat();
  }

  async function handleRefine() {
    const text = refineText.trim();
    if (!text || refining || activeChat) return;
    setRefining(true);
    try {
      const decision = await refine(text);
      if (!decision) return;
      if (decision.kind === "filter") {
        await refilter({
          follower_min: decision.follower_min ?? undefined,
          follower_max: decision.follower_max ?? undefined,
          max_results: decision.max_results ?? undefined,
        });
        setRefineText("");
      } else if (decision.combined_prompt) {
        setRefineText("");
        submit(decision.combined_prompt, activeChatId ?? null);
      }
    } finally {
      setRefining(false);
    }
  }

  const running: RunningEntry | null = busy
    ? { id: "live", title: submittedPrompt || "New search", parentId: runningParentId }
    : null;

  const showEmptyState = !hasLiveRun && !activeChat;

  return (
    <div className="relative flex flex-1 overflow-hidden">
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
        />
      )}

      <div
        className={`fixed inset-y-0 left-0 z-40 transition-transform duration-200 md:static md:z-auto md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <ChatSidebar
          chats={chats}
          activeChatId={activeChatId}
          running={running}
          onSelect={handleSelectChat}
          onNew={handleNewChat}
          onDelete={handleDeleteChat}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      <main className="relative flex flex-1 flex-col overflow-y-auto">
        <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-96 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,var(--color-primary)_0%,transparent_70%)] opacity-[0.08]" />

        <div className="flex items-center gap-2 border-b border-border/60 px-4 py-3 md:hidden">
          <button
            type="button"
            aria-label="Open sidebar"
            onClick={() => setSidebarOpen(true)}
            className="flex size-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
          >
            <Menu className="size-4" />
          </button>
          <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground/70">
            <Sparkles className="size-3.5" />
            KOL Creator Research
          </span>
        </div>

        {showEmptyState ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-6 px-5 py-10 sm:px-8">
            <div className="hidden items-center gap-2 text-muted-foreground/50 sm:flex">
              <Sparkles className="size-4" />
              <span className="text-xs font-medium tracking-wide uppercase">KOL Creator Research</span>
            </div>
            <h1 className="max-w-xl text-center text-xl font-semibold text-foreground/90 sm:text-[26px]">
              Describe the creators you&apos;re looking for.
            </h1>
            <form
              className="flex w-full max-w-xl items-center gap-3 rounded-[10px] border border-border/60 bg-card px-3.5 py-3 sm:px-4.5 sm:py-4"
              onSubmit={(e) => {
                e.preventDefault();
                submit(prompt);
              }}
            >
              <input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. Find finance/trading TikTok creators similar to @valatility and @deltatrendtrading, under 100k followers, real growing engagement"
                className="min-w-0 flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 outline-none"
              />
              <button
                type="submit"
                disabled={!prompt.trim()}
                aria-label="Research creators"
                className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-background transition-opacity disabled:opacity-40"
              >
                <ArrowUp className="size-4" />
              </button>
            </form>
            <div className="flex max-w-xl flex-wrap justify-center gap-2.5">
              {EXAMPLE_PROMPTS.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setPrompt(example)}
                  className="rounded-full border border-border/60 bg-card px-3.5 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
            {activeChat?.parentId && (
              <p className="font-mono text-[11.5px] text-muted-foreground/60">
                ↳ refined from a previous search
              </p>
            )}
            <h2 className="truncate text-base font-semibold text-foreground/92 sm:text-[19px]">
              {displayedTitle}
            </h2>

            {displayedStructuredQuery && (
              <StructuredQueryChips
                query={displayedStructuredQuery}
                editable={!activeChat && status === "done"}
                onFollowerRangeChange={(min, max) => refilter({ follower_min: min, follower_max: max })}
                onMaxResultsChange={(value) => refilter({ max_results: value })}
              />
            )}

            {!activeChat && errors.length > 0 && (
              <div className="space-y-1 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {errors.map((e, i) => (
                  <p key={i}>
                    <span className="font-mono">{e.agent}</span>: {e.message}
                  </p>
                ))}
              </div>
            )}

            {displayedSeedProfile && <SeedProfileCard profile={displayedSeedProfile} />}

            {(activeChat || Object.keys(trace).length > 0) && (
              <ResearchTrace
                trace={displayedTrace}
                live={!activeChat && status === "researching"}
                errors={errors}
                startedAt={activeChat ? null : startedAt}
                finishedAt={activeChat ? (activeChat.elapsedMs != null ? 0 : null) : finishedAt}
                cost={activeChat ? (activeChat.cost ?? null) : cost}
              />
            )}

            {!activeChat && busy && !recomputing && (
              <p className="text-xs text-muted-foreground">{STATUS_LABEL[status]}</p>
            )}

            {recomputing && (
              <div className="flex items-center gap-2">
                <span className="relative flex size-1.5">
                  <span className="status-live absolute inline-flex size-full rounded-full bg-blue-400" />
                  <span className="relative inline-flex size-1.5 rounded-full bg-blue-400" />
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  Recomputing from cache…
                </span>
              </div>
            )}

            {(activeChat || status === "done" || status === "ranking" || recomputing) && (
              <div className={recomputing ? "pointer-events-none opacity-30" : ""}>
                <ShortlistResults shortlist={displayedShortlist} cached={displayedCached} />
              </div>
            )}

            <div className="mt-auto flex items-center gap-2.5 border-t border-border/60 pt-4">
              <form
                className="flex flex-1 items-center rounded-lg border border-border/60 bg-card px-3.5 py-2.5"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleRefine();
                }}
              >
                <input
                  value={refineText}
                  onChange={(e) => setRefineText(e.target.value)}
                  disabled={busy || recomputing || Boolean(activeChat)}
                  placeholder="Refine this search…"
                  className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 outline-none disabled:cursor-not-allowed"
                />
              </form>
              {summary && !activeChat && (
                <span className="tabular hidden shrink-0 font-mono text-[11px] text-muted-foreground/60 sm:inline">
                  {summary.seen} seen
                </span>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

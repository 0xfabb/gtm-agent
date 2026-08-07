"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Search, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatSidebar } from "@/components/research/ChatSidebar";
import { PipelineStepper } from "@/components/research/PipelineStepper";
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
} from "@/lib/chatHistory";
import { useResearchStream } from "@/lib/useResearchStream";

const STATUS_LABEL: Record<string, string> = {
  idle: "",
  structuring: "Structuring your request…",
  researching: "Researching creators live…",
  ranking: "Ranking candidates…",
  done: "Done",
  error: "Something went wrong",
};

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const savedRef = useRef(false);

  const chats = useSyncExternalStore(subscribeChats, getChatsSnapshot, getServerChatsSnapshot);
  const {
    status,
    structuredQuery,
    seedProfile,
    trace,
    shortlist,
    unverified,
    summary,
    errors,
    start,
    reset,
  } = useResearchStream();

  useEffect(() => {
    if (status === "done" && !savedRef.current && submittedPrompt) {
      savedRef.current = true;
      const id = newChatId();
      saveChat({
        id,
        prompt: submittedPrompt,
        createdAt: Date.now(),
        structuredQuery,
        seedProfile,
        trace,
        shortlist,
        unverified,
      });
      setActiveChatId(id);
    }
  }, [status, submittedPrompt, structuredQuery, seedProfile, trace, shortlist, unverified]);

  const activeChat = activeChatId ? (chats.find((c) => c.id === activeChatId) ?? null) : null;
  const busy = status === "structuring" || status === "researching" || status === "ranking";

  const displayedStructuredQuery = activeChat ? activeChat.structuredQuery : structuredQuery;
  const displayedTrace = activeChat ? activeChat.trace : trace;
  const displayedShortlist = activeChat ? activeChat.shortlist : shortlist;
  const displayedUnverified = activeChat ? (activeChat.unverified ?? []) : unverified;
  const displayedSeedProfile = activeChat ? (activeChat.seedProfile ?? null) : seedProfile;

  function submit() {
    if (!prompt.trim() || busy) return;
    savedRef.current = false;
    setSubmittedPrompt(prompt.trim());
    setActiveChatId(null);
    start(prompt.trim());
  }

  function handleNewChat() {
    reset();
    setActiveChatId(null);
    setPrompt("");
    savedRef.current = false;
  }

  function handleSelectChat(id: string) {
    reset();
    setActiveChatId(id);
    const chat = chats.find((c) => c.id === id);
    if (chat) setPrompt(chat.prompt);
  }

  function handleDeleteChat(id: string) {
    deleteChat(id);
    if (activeChatId === id) handleNewChat();
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      <ChatSidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelect={handleSelectChat}
        onNew={handleNewChat}
        onDelete={handleDeleteChat}
      />

      <main className="relative flex flex-1 flex-col overflow-y-auto">
        <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-96 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,var(--color-primary)_0%,transparent_70%)] opacity-[0.08]" />

        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-12">
          <header className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-primary">
              <Sparkles className="size-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">KOL Creator Research</h1>
              <p className="text-sm text-muted-foreground">
                Describe the creators you&apos;re looking for — watch it research live.
              </p>
            </div>
          </header>

          <form
            className="focus-within:ring-primary/30 flex flex-col gap-3 rounded-xl border border-border/60 bg-card/40 p-3 transition-shadow focus-within:ring-2"
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
          >
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  submit();
                }
              }}
              placeholder="e.g. Find finance and trading TikTok creators, US audience, mostly male, 18 to 24, under 100k followers, growing fast."
              rows={3}
              disabled={busy}
              className="resize-none border-0 bg-transparent px-1 shadow-none focus-visible:ring-0"
            />
            <div className="flex items-center justify-between gap-3">
              <kbd className="hidden rounded border border-border/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:inline-block">
                ⌘ + Enter
              </kbd>
              <Button type="submit" disabled={busy || !prompt.trim()} className="gap-1.5">
                <Search className="size-3.5" />
                {busy ? "Researching…" : "Research creators"}
              </Button>
            </div>
          </form>

          {!activeChat && status !== "idle" && (
            <div className="animate-in fade-in duration-500">
              <PipelineStepper status={status} />
              {STATUS_LABEL[status] && (
                <p className="mt-2 text-center text-xs text-muted-foreground">
                  {STATUS_LABEL[status]}
                </p>
              )}
            </div>
          )}

          {!activeChat && errors.length > 0 && (
            <div className="animate-in fade-in space-y-1 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {errors.map((e, i) => (
                <p key={i}>
                  <span className="font-mono">{e.agent}</span>: {e.message}
                </p>
              ))}
            </div>
          )}

          {displayedStructuredQuery && <StructuredQueryChips query={displayedStructuredQuery} />}

          {displayedSeedProfile && <SeedProfileCard profile={displayedSeedProfile} />}

          {(activeChat || (status !== "idle" && status !== "structuring")) && (
            <ResearchTrace trace={displayedTrace} live={!activeChat && status === "researching"} />
          )}

          {(activeChat || status === "done" || status === "ranking") && (
            <ShortlistResults
              shortlist={displayedShortlist}
              unverified={displayedUnverified}
              summary={activeChat ? null : summary}
            />
          )}
        </div>
      </main>
    </div>
  );
}

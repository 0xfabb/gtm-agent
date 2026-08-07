import { MessageSquare, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ChatSession } from "@/lib/chatHistory";

function formatRelativeTime(ts: number): string {
  const diffMs = Date.now() - ts;
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export function ChatSidebar({
  chats,
  activeChatId,
  onSelect,
  onNew,
  onDelete,
}: {
  chats: ChatSession[];
  activeChatId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col gap-3 border-r border-border/60 bg-card/20 p-3">
      <Button
        variant="secondary"
        className="w-full justify-start gap-2"
        onClick={onNew}
      >
        <Plus className="size-4" />
        New chat
      </Button>

      <div className="flex-1 space-y-1 overflow-y-auto">
        {chats.length === 0 && (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">
            No previous research yet
          </p>
        )}
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={cn(
              "group/chat flex items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors",
              chat.id === activeChatId
                ? "bg-primary/10 text-foreground"
                : "text-muted-foreground hover:bg-card/60 hover:text-foreground"
            )}
          >
            <button
              type="button"
              onClick={() => onSelect(chat.id)}
              className="flex flex-1 items-center gap-2 overflow-hidden text-left"
            >
              <MessageSquare className="size-3.5 shrink-0" />
              <span className="flex-1 truncate">{chat.prompt}</span>
            </button>
            <span className="shrink-0 text-[10px] text-muted-foreground">
              {formatRelativeTime(chat.createdAt)}
            </span>
            <button
              type="button"
              onClick={() => onDelete(chat.id)}
              className="shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover/chat:opacity-100"
              aria-label="Delete chat"
            >
              <X className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}

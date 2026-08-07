import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ChatSession } from "@/lib/chatHistory";

function formatDate(ts: number): string {
  const diffMs = Date.now() - ts;
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days === 1) return "yesterday";
  if (days < 7) return `${days}d ago`;
  return new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function isToday(ts: number): boolean {
  const d = new Date(ts);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

interface RunItemProps {
  title: string;
  metaText: string;
  active: boolean;
  isChild: boolean;
  isRunning: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}

function RunItem({ title, metaText, active, isChild, isRunning, onSelect, onDelete }: RunItemProps) {
  return (
    <div
      className={cn(
        "group/chat relative flex flex-col gap-0.5 rounded-md px-2.5 py-2 text-left transition-colors",
        isChild && "ml-4 before:absolute before:-left-2 before:-top-1.5 before:bottom-3.5 before:w-px before:bg-border/60",
        active ? "bg-primary/10" : "hover:bg-white/2"
      )}
    >
      <button type="button" onClick={onSelect} className="flex flex-col gap-0.5 text-left">
        <span
          className={cn(
            "truncate text-[13px] font-medium",
            active ? "text-foreground" : "text-foreground/70"
          )}
        >
          {title}
        </span>
        <span className="flex items-center gap-1.5">
          {isRunning && (
            <span className="relative flex size-1.5 shrink-0">
              <span className="status-live absolute inline-flex size-full rounded-full bg-blue-400" />
              <span className="relative inline-flex size-1.5 rounded-full bg-blue-400" />
            </span>
          )}
          <span className="tabular font-mono text-[11px] text-muted-foreground">
            {isRunning ? "Running…" : metaText}
          </span>
        </span>
      </button>
      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          aria-label="Delete run"
          className="absolute right-1.5 top-1.5 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover/chat:opacity-100"
        >
          <X className="size-3" />
        </button>
      )}
    </div>
  );
}

export interface RunningEntry {
  id: string;
  title: string;
  parentId?: string | null;
}

export function ChatSidebar({
  chats,
  activeChatId,
  running,
  onSelect,
  onNew,
  onDelete,
}: {
  chats: ChatSession[];
  activeChatId: string | null;
  running: RunningEntry | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  const today = chats.filter((c) => isToday(c.createdAt));
  const earlier = chats.filter((c) => !isToday(c.createdAt));

  const empty = chats.length === 0 && !running;

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col gap-4 border-r border-border/60 bg-sidebar p-3">
      <div className="flex items-center justify-between px-1 pt-1">
        <span className="text-[13px] font-semibold text-foreground/90">Runs</span>
      </div>

      <Button variant="outline" className="w-full justify-center gap-2" onClick={onNew}>
        <Plus className="size-3.5" />
        New search
      </Button>

      <div className="flex-1 space-y-4 overflow-y-auto">
        {empty && (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">
            No previous research yet
          </p>
        )}

        {(running || today.length > 0) && (
          <div className="space-y-1">
            <p className="px-2 font-mono text-[11px] font-medium tracking-wide text-muted-foreground/60 uppercase">
              Today
            </p>
            {running && (
              <RunItem
                title={running.title}
                metaText=""
                active
                isChild={Boolean(running.parentId)}
                isRunning
                onSelect={() => {}}
              />
            )}
            {today.map((chat) => (
              <RunItem
                key={chat.id}
                title={chat.prompt}
                metaText={`${chat.shortlist.length} results · ${formatDate(chat.createdAt)}`}
                active={chat.id === activeChatId}
                isChild={Boolean(chat.parentId)}
                isRunning={false}
                onSelect={() => onSelect(chat.id)}
                onDelete={() => onDelete(chat.id)}
              />
            ))}
          </div>
        )}

        {earlier.length > 0 && (
          <div className="space-y-1">
            <p className="px-2 font-mono text-[11px] font-medium tracking-wide text-muted-foreground/60 uppercase">
              Earlier
            </p>
            {earlier.map((chat) => (
              <RunItem
                key={chat.id}
                title={chat.prompt}
                metaText={`${chat.shortlist.length} results · ${formatDate(chat.createdAt)}`}
                active={chat.id === activeChatId}
                isChild={Boolean(chat.parentId)}
                isRunning={false}
                onSelect={() => onSelect(chat.id)}
                onDelete={() => onDelete(chat.id)}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

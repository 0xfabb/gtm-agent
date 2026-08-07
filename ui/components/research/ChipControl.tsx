"use client";

import { useEffect, useRef, useState } from "react";
import { Pencil } from "lucide-react";
import { cn } from "@/lib/utils";

const FOLLOWER_STOPS = [
  0, 1_000, 2_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000,
  1_000_000, 2_000_000, 5_000_000, 10_000_000,
];

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n % 1_000_000 === 0 ? 0 : 1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n % 1_000 === 0 ? 0 : 1)}K`;
  return String(n);
}

function nearestStopIndex(value: number): number {
  let closest = 0;
  let closestDiff = Infinity;
  FOLLOWER_STOPS.forEach((stop, i) => {
    const diff = Math.abs(stop - value);
    if (diff < closestDiff) {
      closestDiff = diff;
      closest = i;
    }
  });
  return closest;
}

function indexToPercent(i: number): number {
  return (i / (FOLLOWER_STOPS.length - 1)) * 100;
}

export function Chip({
  label,
  prominent,
  onClick,
}: {
  label: string;
  prominent?: boolean;
  onClick?: () => void;
}) {
  const editable = Boolean(onClick);
  return (
    <button
      type="button"
      disabled={!editable}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border bg-popover px-2.5 py-1.5 font-mono text-[13px] font-medium whitespace-nowrap text-foreground/80 transition-colors",
        prominent ? "border-primary/35" : "border-border/60",
        editable && "hover:border-primary/40 hover:text-foreground"
      )}
    >
      <span>{label}</span>
      {editable && (
        <Pencil className={cn("size-2.5", prominent ? "text-primary" : "text-muted-foreground/60")} />
      )}
    </button>
  );
}

export function FollowerRangeChip({
  min,
  max,
  onApply,
}: {
  min: number;
  max: number;
  onApply: (min: number, max: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const [minIdx, setMinIdx] = useState(nearestStopIndex(min));
  const [maxIdx, setMaxIdx] = useState(nearestStopIndex(max));
  const [dragging, setDragging] = useState<"min" | "max" | null>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  function openEditor() {
    setMinIdx(nearestStopIndex(min));
    setMaxIdx(nearestStopIndex(max));
    setOpen(true);
  }

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        onApply(FOLLOWER_STOPS[minIdx], FOLLOWER_STOPS[maxIdx]);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open, minIdx, maxIdx, onApply]);

  function percentFromEvent(clientX: number): number {
    const rect = trackRef.current?.getBoundingClientRect();
    if (!rect) return 0;
    return Math.min(100, Math.max(0, ((clientX - rect.left) / rect.width) * 100));
  }

  function indexFromPercent(pct: number): number {
    return Math.round((pct / 100) * (FOLLOWER_STOPS.length - 1));
  }

  useEffect(() => {
    if (!dragging) return;

    function handleMove(e: PointerEvent) {
      const idx = indexFromPercent(percentFromEvent(e.clientX));
      if (dragging === "min") {
        setMinIdx(Math.min(idx, maxIdx));
      } else {
        setMaxIdx(Math.max(idx, minIdx));
      }
    }
    function handleUp() {
      setDragging(null);
    }
    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp);
    return () => {
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };
  }, [dragging, minIdx, maxIdx]);

  const label = `${formatCount(FOLLOWER_STOPS[nearestStopIndex(min)])} – ${formatCount(FOLLOWER_STOPS[nearestStopIndex(max)])} followers`;

  if (!open) {
    return <Chip label={label} onClick={openEditor} />;
  }

  const minPct = indexToPercent(minIdx);
  const maxPct = indexToPercent(maxIdx);

  return (
    <div
      ref={containerRef}
      className="relative z-10 inline-flex min-w-[230px] flex-col gap-3 rounded-lg border border-primary/40 bg-popover px-3.5 py-3 font-sans"
    >
      <span className="font-mono text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
        Followers
      </span>
      <div className="flex items-center gap-2">
        <span className="rounded-md border border-border/60 bg-background px-2 py-1 font-mono text-[13px] tabular text-foreground/90">
          {FOLLOWER_STOPS[minIdx].toLocaleString()}
        </span>
        <span className="text-xs text-muted-foreground/60">–</span>
        <span className="rounded-md border border-border/60 bg-background px-2 py-1 font-mono text-[13px] tabular text-foreground/90">
          {FOLLOWER_STOPS[maxIdx].toLocaleString()}
        </span>
      </div>
      <div ref={trackRef} className="relative mt-1.5 flex h-3.5 items-center">
        <div className="absolute inset-x-0 h-[3px] rounded-full bg-white/10" />
        <div
          className="absolute h-[3px] rounded-full bg-primary"
          style={{ left: `${minPct}%`, right: `${100 - maxPct}%` }}
        />
        <button
          type="button"
          aria-label="Minimum followers"
          onPointerDown={() => setDragging("min")}
          className="absolute size-3 -translate-x-1/2 cursor-grab rounded-full bg-white shadow active:cursor-grabbing"
          style={{ left: `${minPct}%` }}
        />
        <button
          type="button"
          aria-label="Maximum followers"
          onPointerDown={() => setDragging("max")}
          className="absolute size-3 -translate-x-1/2 cursor-grab rounded-full bg-white shadow ring-4 ring-primary/25 active:cursor-grabbing"
          style={{ left: `${maxPct}%` }}
        />
      </div>
      <p className="max-w-[220px] text-[11px] leading-relaxed text-muted-foreground">
        Releasing re-filters the cached candidates instantly — no new research.
      </p>
    </div>
  );
}

export function MaxResultsChip({
  value,
  onApply,
}: {
  value: number;
  onApply: (value: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(String(value));
  const containerRef = useRef<HTMLDivElement>(null);

  function openEditor() {
    setDraft(String(value));
    setOpen(true);
  }

  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        commit();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, draft]);

  function commit() {
    setOpen(false);
    const parsed = Math.max(1, Math.min(50, parseInt(draft, 10) || value));
    onApply(parsed);
  }

  if (!open) {
    return <Chip label={`Top ${value} results`} prominent onClick={openEditor} />;
  }

  return (
    <div
      ref={containerRef}
      className="inline-flex items-center gap-2 rounded-lg border border-primary/40 bg-popover px-3 py-2"
    >
      <span className="font-mono text-[11px] text-muted-foreground">Top</span>
      <input
        autoFocus
        type="number"
        min={1}
        max={50}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && commit()}
        className="w-12 rounded border border-border/60 bg-background px-1.5 py-0.5 text-center font-mono text-[13px] tabular text-foreground outline-none focus:border-primary/50"
      />
      <span className="font-mono text-[11px] text-muted-foreground">results</span>
    </div>
  );
}

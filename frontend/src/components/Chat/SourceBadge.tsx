"use client";

import { Database, GitMerge, Search } from "lucide-react";

import type { RoutingSource } from "@/lib/api";

type SourceBadgeProps = {
  source?: RoutingSource;
};

export function SourceBadge({ source }: SourceBadgeProps) {
  if (!source) {
    return null;
  }

  const isSql = source === "sql";
  const isBoth = source === "both";
  const Icon = isBoth ? GitMerge : isSql ? Database : Search;

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
      <Icon className="h-3 w-3" />
      {isBoth ? "Both" : isSql ? "SQL" : "Vector"}
    </span>
  );
}

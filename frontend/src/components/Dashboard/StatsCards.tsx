"use client";

import { Database, FileStack, Layers3 } from "lucide-react";

import type { KnowledgeStats } from "@/lib/api";

type StatsCardsProps = {
  stats: KnowledgeStats;
};

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      label: "Documents",
      value: stats.total_documents,
      icon: FileStack,
    },
    {
      label: "Chunks",
      value: stats.total_chunks,
      icon: Layers3,
    },
    {
      label: "Lignes SQL",
      value: stats.total_records,
      icon: Database,
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <article
            key={card.label}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/80"
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-600 dark:text-slate-400">{card.label}</span>
              <Icon className="h-4 w-4 text-slate-500 dark:text-slate-300" />
            </div>
            <strong className="text-3xl font-semibold text-slate-900 dark:text-white">
              {card.value}
            </strong>
          </article>
        );
      })}
    </div>
  );
}

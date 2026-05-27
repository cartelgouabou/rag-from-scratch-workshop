"use client";

import useSWR from "swr";

import { ChatWindow } from "@/components/Chat/ChatWindow";
import { KnowledgeTable } from "@/components/Dashboard/KnowledgeTable";
import { StatsCards } from "@/components/Dashboard/StatsCards";
import { getKnowledgeOverview } from "@/lib/api";

export default function DashboardPage() {
  const { data, error, isLoading } = useSWR("knowledge-overview", getKnowledgeOverview);

  const stats = data?.stats ?? {
    total_documents: 0,
    total_chunks: 0,
    total_records: 0,
    chroma_size_mb: 0,
    sqlite_size_mb: 0,
  };
  const documents = data?.documents ?? [];

  return (
    <main className="grid gap-6 lg:grid-cols-[1.05fr_1.15fr]">
      <section className="space-y-6">
        <StatsCards stats={stats} />
        <div className="rounded-3xl border border-slate-200 bg-white/80 p-5 dark:border-slate-800 dark:bg-slate-900/70">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">État de la base</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            {isLoading
              ? "Chargement des statistiques..."
              : error
                ? "Impossible de charger l'état courant de la base."
                : `ChromaDB: ${stats.chroma_size_mb} MB • SQLite: ${stats.sqlite_size_mb} MB`}
          </p>
        </div>
        <KnowledgeTable documents={documents} />
      </section>

      <ChatWindow documentCount={documents.length} />
    </main>
  );
}

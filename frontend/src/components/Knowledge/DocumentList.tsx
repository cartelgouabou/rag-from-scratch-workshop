"use client";

import { Loader2, RefreshCw, Trash2 } from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { deleteDocument, purgeAllKnowledge, reindexDocument, type DocumentItem } from "@/lib/api";

type DocumentListProps = {
  documents: DocumentItem[];
  onRefresh: () => Promise<void> | void;
};

export function DocumentList({ documents, onRefresh }: DocumentListProps) {
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPurgeDialogOpen, setIsPurgeDialogOpen] = useState(false);
  const [isPurging, setIsPurging] = useState(false);

  async function handleDelete(document: DocumentItem) {
    const confirmed = window.confirm(
      `Supprimer ${document.filename} de la base vectorielle et SQLite ?`,
    );
    if (!confirmed) {
      return;
    }

    setBusyDocumentId(document.id);
    try {
      await deleteDocument(document.id);
      await onRefresh();
    } finally {
      setBusyDocumentId(null);
    }
  }

  async function handleReindex(document: DocumentItem) {
    setBusyDocumentId(document.id);
    try {
      await reindexDocument(document.id);
      await onRefresh();
    } finally {
      setBusyDocumentId(null);
    }
  }

  async function handleRefresh() {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  }

  async function handlePurgeConfirm() {
    setIsPurging(true);
    try {
      await purgeAllKnowledge();
      setIsPurgeDialogOpen(false);
      await onRefresh();
    } finally {
      setIsPurging(false);
    }
  }

  return (
    <>
      <section className="rounded-3xl border border-slate-200 bg-white/80 p-5 dark:border-slate-800 dark:bg-slate-900/70">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Documents indexés</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              La reindexation rejoue le fichier source dans la collection active. La suppression efface le
              document du store vectoriel, du store SQL et du stockage source.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setIsPurgeDialogOpen(true)}
              disabled={documents.length === 0 || isPurging || busyDocumentId !== null}
              className="inline-flex items-center gap-2 rounded-2xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-rose-400/20 dark:bg-rose-500/10 dark:text-rose-200 dark:hover:bg-rose-500/20"
            >
              <Trash2 className="h-4 w-4" />
              Tout supprimer
            </button>
            <button
              type="button"
              onClick={handleRefresh}
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Actualiser
            </button>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-slate-600 dark:bg-slate-950/80 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Nom</th>
                <th className="px-4 py-3 font-medium">Chunks</th>
                <th className="px-4 py-3 font-medium">Indexé le</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white/50 text-slate-900 dark:divide-slate-800 dark:bg-slate-950/30 dark:text-slate-100">
              {documents.length > 0 ? (
                documents.map((document) => (
                  <tr key={document.id}>
                    <td className="px-4 py-3 uppercase text-slate-600 dark:text-slate-300">
                      {document.type}
                    </td>
                    <td className="px-4 py-3">{document.filename}</td>
                    <td className="px-4 py-3">{document.nb_chunks}</td>
                    <td className="px-4 py-3">
                      {new Date(document.indexed_at).toLocaleString("fr-FR")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleReindex(document)}
                          disabled={!document.can_reindex || busyDocumentId === document.id}
                          className="inline-flex items-center gap-2 rounded-xl border border-indigo-400/20 bg-indigo-500/10 px-3 py-2 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:text-indigo-100"
                        >
                          {busyDocumentId === document.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
                          )}
                          Reindexer
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(document)}
                          disabled={busyDocumentId === document.id}
                          className="inline-flex items-center gap-2 rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-700 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:text-rose-200"
                        >
                          {busyDocumentId === document.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                          Supprimer
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-slate-500 dark:text-slate-400">
                    Aucun document indexé pour l'instant.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <ConfirmDialog
        open={isPurgeDialogOpen}
        title="Supprimer toutes les données ?"
        description="Cette action supprimera définitivement tous les documents indexés, les chunks vectoriels (Chroma), les tables SQL associées et les fichiers sources. Cette opération est irréversible."
        confirmLabel="Oui, tout supprimer"
        onConfirm={handlePurgeConfirm}
        onCancel={() => setIsPurgeDialogOpen(false)}
        isLoading={isPurging}
        variant="danger"
      />
    </>
  );
}

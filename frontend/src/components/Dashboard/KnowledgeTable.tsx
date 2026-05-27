"use client";

import type { DocumentItem } from "@/lib/api";

type KnowledgeTableProps = {
  documents: DocumentItem[];
};

export function KnowledgeTable({ documents }: KnowledgeTableProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white/80 p-5 dark:border-slate-800 dark:bg-slate-900/70">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Documents indexés</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Vue synthétique de la base de connaissance disponible.
        </p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800">
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
          <thead className="bg-slate-50 text-left text-slate-600 dark:bg-slate-950/80 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Nom</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Chunks</th>
              <th className="px-4 py-3 font-medium">Lignes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white/50 text-slate-900 dark:divide-slate-800 dark:bg-slate-950/30 dark:text-slate-100">
            {documents.length > 0 ? (
              documents.map((document) => (
                <tr key={document.id}>
                  <td className="px-4 py-3">{document.filename}</td>
                  <td className="px-4 py-3 uppercase text-slate-600 dark:text-slate-300">
                    {document.type}
                  </td>
                  <td className="px-4 py-3">{document.nb_chunks}</td>
                  <td className="px-4 py-3">{document.nb_records}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-slate-500 dark:text-slate-400">
                  Aucun document n'a encore été indexé.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

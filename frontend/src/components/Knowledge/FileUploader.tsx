"use client";

import { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Loader2, UploadCloud } from "lucide-react";

import { uploadDocument } from "@/lib/api";

type UploadItem = {
  id: string;
  file: File;
  progress: number;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
};

type FileUploaderProps = {
  onUploaded: () => Promise<void> | void;
};

export function FileUploader({ onUploaded }: FileUploaderProps) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const dropzone = useDropzone({
    multiple: true,
    accept: {
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/webp": [".webp"],
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    onDrop(acceptedFiles) {
      setItems((current) => [
        ...current,
        ...acceptedFiles.map((file) => ({
          id: `${file.name}-${file.size}-${file.lastModified}`,
          file,
          progress: 0,
          status: "pending" as const,
        })),
      ]);
    },
  });

  const hasItems = items.length > 0;
  const pendingCount = useMemo(
    () => items.filter((item) => item.status === "pending").length,
    [items],
  );

  async function handleUpload() {
    if (!hasItems || isUploading) {
      return;
    }

    setIsUploading(true);
    for (const item of items) {
      if (item.status === "done") {
        continue;
      }

      updateItem(item.id, { status: "uploading", progress: 20, error: undefined });
      try {
        updateItem(item.id, { progress: 60 });
        await uploadDocument(item.file);
        updateItem(item.id, { status: "done", progress: 100 });
      } catch (error) {
        updateItem(item.id, {
          status: "error",
          progress: 100,
          error: error instanceof Error ? error.message : "Upload failed",
        });
      }
    }

    await onUploaded();
    setIsUploading(false);
  }

  function updateItem(id: string, patch: Partial<UploadItem>) {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white/80 p-5 dark:border-slate-800 dark:bg-slate-900/70">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Ajouter des données</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          PDF, images, CSV et Excel sont pris en charge. L'OCR et l'indexation se font pendant l'upload, ce qui peut prendre un peu plus de temps pour les PDF scannes et les images.
        </p>
      </div>

      <div
        {...dropzone.getRootProps()}
        className="cursor-pointer rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center transition hover:border-indigo-400 dark:border-slate-700 dark:bg-slate-950/60"
      >
        <input {...dropzone.getInputProps()} />
        <UploadCloud className="mx-auto mb-4 h-10 w-10 text-indigo-500 dark:text-indigo-300" />
        <p className="text-base font-medium text-slate-900 dark:text-white">
          Glissez vos fichiers ici ou cliquez pour sélectionner
        </p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Formats supportes : PDF, PNG, JPG, JPEG, WEBP, CSV, XLSX, XLS
        </p>
      </div>

      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50"
          >
            <div className="mb-2 flex items-center justify-between gap-4 text-sm text-slate-800 dark:text-slate-200">
              <span>{item.file.name}</span>
              <span className="uppercase text-slate-500 dark:text-slate-400">{item.status}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
              <div
                className={`h-full rounded-full transition-all ${
                  item.status === "error" ? "bg-rose-400" : "bg-indigo-400"
                }`}
                style={{ width: `${item.progress}%` }}
              />
            </div>
            {item.error ? (
              <p className="mt-2 text-xs text-rose-600 dark:text-rose-300">{item.error}</p>
            ) : null}
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={handleUpload}
        disabled={!hasItems || isUploading}
        className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-indigo-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
      >
        {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        {pendingCount > 0 ? `Uploader ${pendingCount} fichier(s)` : "Actualiser"}
      </button>
    </section>
  );
}

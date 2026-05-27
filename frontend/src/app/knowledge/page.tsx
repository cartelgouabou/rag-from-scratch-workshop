"use client";

import useSWR from "swr";

import { DocumentList } from "@/components/Knowledge/DocumentList";
import { FileUploader } from "@/components/Knowledge/FileUploader";
import { getKnowledgeOverview } from "@/lib/api";

export default function KnowledgePage() {
  const { data, mutate } = useSWR("knowledge-overview", getKnowledgeOverview);

  async function refreshOverview() {
    await mutate();
  }

  return (
    <main className="space-y-6">
      <FileUploader onUploaded={refreshOverview} />
      <DocumentList documents={data?.documents ?? []} onRefresh={refreshOverview} />
    </main>
  );
}

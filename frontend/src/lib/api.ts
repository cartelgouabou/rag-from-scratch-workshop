export type RoutingSource = "sql" | "vector" | "both";

export type ChatSource = {
  title: string;
  detail?: string;
  excerpt?: string;
  origin?: RoutingSource;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  source?: RoutingSource;
  sources?: ChatSource[];
};

export type DocumentItem = {
  id: string;
  filename: string;
  type: string;
  nb_chunks: number;
  nb_records: number;
  indexed_at: string;
  can_reindex: boolean;
};

export type KnowledgeStats = {
  total_documents: number;
  total_chunks: number;
  total_records: number;
  chroma_size_mb: number;
  sqlite_size_mb: number;
};

export type KnowledgeOverview = {
  documents: DocumentItem[];
  stats: KnowledgeStats;
};

export type IngestResponse = {
  document_id: string;
  filename: string;
  type: string;
  nb_chunks: number;
  nb_records: number;
  duration_ms: number;
};

export type ReindexResponse = IngestResponse;

export type PurgeResponse = {
  success: boolean;
  deleted_documents: number;
};

type StreamHandlers = {
  onRouting?: (decision: RoutingSource) => void;
  onToken?: (token: string) => void;
  onDone?: (source: RoutingSource, sources: ChatSource[]) => void;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "API request failed");
  }
  return (await response.json()) as T;
}

export async function getKnowledgeOverview(): Promise<KnowledgeOverview> {
  const response = await fetch(`${API_URL}/api/knowledge/documents`, {
    cache: "no-store",
  });
  return parseJson<KnowledgeOverview>(response);
}

export async function uploadDocument(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/api/ingest/upload`, {
    method: "POST",
    body: formData,
  });
  return parseJson<IngestResponse>(response);
}

export async function purgeAllKnowledge(): Promise<PurgeResponse> {
  const response = await fetch(`${API_URL}/api/knowledge/purge`, {
    method: "DELETE",
  });
  return parseJson<PurgeResponse>(response);
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/knowledge/documents/${documentId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Delete failed");
  }
}

export async function reindexDocument(documentId: string): Promise<ReindexResponse> {
  const response = await fetch(`${API_URL}/api/knowledge/documents/${documentId}/reindex`, {
    method: "POST",
  });
  return parseJson<ReindexResponse>(response);
}

export async function streamChat(
  message: string,
  history: ChatMessage[],
  handlers: StreamHandlers,
): Promise<void> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, history }),
  });

  if (!response.ok || !response.body) {
    const messageText = await response.text();
    throw new Error(messageText || "Streaming request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const event of events) {
      const dataLine = event
        .split("\n")
        .find((line) => line.startsWith("data:"));

      if (!dataLine) {
        continue;
      }

      const payload = JSON.parse(dataLine.replace(/^data:\s*/, ""));
      if (payload.type === "routing") {
        handlers.onRouting?.(payload.decision as RoutingSource);
      } else if (payload.type === "token") {
        handlers.onToken?.(payload.content as string);
      } else if (payload.type === "done") {
        handlers.onDone?.(
          payload.source as RoutingSource,
          (payload.sources as ChatSource[] | undefined) ?? [],
        );
      }
    }
  }
}

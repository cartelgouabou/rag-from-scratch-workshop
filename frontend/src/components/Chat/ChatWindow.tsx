"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Loader2, MessageSquarePlus, SendHorizontal } from "lucide-react";

import { ChatMessage, streamChat } from "@/lib/api";

import { MessageBubble } from "./MessageBubble";

type ChatWindowProps = {
  documentCount: number;
};

const initialMessage: ChatMessage = {
  role: "assistant",
  content:
    "Bonjour. Posez-moi une question sur vos documents. Je choisirai automatiquement un flux SQL, VECTOR ou BOTH selon votre demande.",
};

export function ChatWindow({ documentCount }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const scrollAnchorRef = useRef<HTMLDivElement | null>(null);

  const helperText = useMemo(() => {
    if (documentCount === 0) {
      return "Ajoutez d'abord un document dans l'onglet Knowledge pour obtenir des réponses utiles.";
    }
    return `${documentCount} document(s) indexé(s).`;
  }, [documentCount]);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function clearConversation() {
    if (isSending) {
      return;
    }
    setMessages([initialMessage]);
    setInput("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) {
      return;
    }

    const userMessage: ChatMessage = { role: "user", content: trimmed };
    const assistantPlaceholder: ChatMessage = { role: "assistant", content: "" };
    const history = messages.filter((message) => message.content.trim().length > 0);

    setInput("");
    setIsSending(true);
    setMessages((current) => [...current, userMessage, assistantPlaceholder]);

    try {
      await streamChat(trimmed, history, {
        onRouting(decision) {
          setMessages((current) => updateLastAssistant(current, { source: decision }));
        },
        onToken(token) {
          setMessages((current) =>
            updateLastAssistant(current, {
              content: `${current[current.length - 1]?.content ?? ""}${token}`,
            }),
          );
        },
        onDone(source, sources) {
          setMessages((current) => updateLastAssistant(current, { source, sources }));
        },
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Une erreur est survenue pendant le streaming.";
      setMessages((current) =>
        updateLastAssistant(current, {
          content: message,
        }),
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="flex h-full min-h-[640px] flex-col rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-2xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-slate-950/40">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Chat</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">{helperText}</p>
        </div>
        <button
          type="button"
          onClick={clearConversation}
          disabled={isSending}
          aria-label="Nouvelle conversation"
          title="Nouvelle conversation"
          className="inline-flex shrink-0 items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2 text-sm text-slate-600 transition hover:border-indigo-300 hover:text-indigo-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:border-indigo-400 dark:hover:text-white"
        >
          <MessageSquarePlus className="h-4 w-4" />
          Nouvelle conversation
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.map((message, index) => (
          <MessageBubble key={`${message.role}-${index}`} message={message} />
        ))}
        <div ref={scrollAnchorRef} />
      </div>

      <form onSubmit={handleSubmit} className="mt-4 flex gap-3">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Posez votre question..."
          rows={3}
          className="min-h-[88px] flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100"
        />
        <button
          type="submit"
          disabled={isSending || input.trim().length === 0}
          className="inline-flex min-w-[120px] items-center justify-center gap-2 rounded-2xl bg-indigo-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
        >
          {isSending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Envoi
            </>
          ) : (
            <>
              <SendHorizontal className="h-4 w-4" />
              Send
            </>
          )}
        </button>
      </form>
    </section>
  );
}

function updateLastAssistant(messages: ChatMessage[], update: Partial<ChatMessage>) {
  const next = [...messages];
  for (let index = next.length - 1; index >= 0; index -= 1) {
    if (next[index]?.role === "assistant") {
      next[index] = {
        ...next[index],
        ...update,
      };
      break;
    }
  }
  return next;
}

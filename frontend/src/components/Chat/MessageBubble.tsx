"use client";

import { Bot, User } from "lucide-react";

import type { ChatMessage } from "@/lib/api";

import { SourceBadge } from "./SourceBadge";

type MessageBubbleProps = {
  message: ChatMessage;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={`flex gap-3 ${isAssistant ? "justify-start" : "justify-end"}`}
    >
      {isAssistant && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-600 dark:text-indigo-200">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-2xl border px-4 py-3 text-sm leading-6 shadow-sm ${
          isAssistant
            ? "border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100"
            : "border-indigo-500/40 bg-indigo-500 text-white"
        }`}
      >
        <div className="mb-2 flex items-center justify-between gap-3">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
            {isAssistant ? "Assistant" : "Vous"}
          </span>
          {isAssistant ? (
            <SourceBadge source={message.source} />
          ) : (
            <User className="h-3.5 w-3.5 text-white/80" />
          )}
        </div>
        <p className="whitespace-pre-wrap">{message.content}</p>
        {isAssistant && message.sources && message.sources.length > 0 ? (
          <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-800">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Sources utilisees
            </p>
            <div className="space-y-2">
              {message.sources.map((source, index) => (
                <div
                  key={`${source.title}-${index}`}
                  className="rounded-xl border border-slate-200 bg-white/80 p-3 dark:border-slate-800 dark:bg-slate-900/70"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                      {source.title}
                    </p>
                    {source.origin ? (
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        {source.origin}
                      </span>
                    ) : null}
                  </div>
                  {source.detail ? (
                    <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">{source.detail}</p>
                  ) : null}
                  {source.excerpt ? (
                    <p className="mt-2 text-xs leading-5 text-slate-700 dark:text-slate-300">
                      {source.excerpt}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

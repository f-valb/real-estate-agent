"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Brain, ChevronDown, ChevronUp, RotateCcw, Loader2 } from "lucide-react";
import { chatHomeFinder } from "@/lib/api";
import type { ChatMessage, HomefinderResult } from "@/lib/types";
import HomeFinderResults from "@/components/HomeFinderResults";

const INITIAL_MESSAGE: ChatMessage = {
  role: "assistant",
  content:
    "Hi! I'm your AI home finder 🏡 Tell me about your ideal home — where would you love to live, and what matters most to you?",
};

function ThoughtBubble({ thought }: { thought: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-1.5 mb-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-brand-500 transition-colors"
      >
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        💭 Reasoning
      </button>
      {open && (
        <div className="mt-1 text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 leading-relaxed max-w-sm">
          {thought}
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 mb-4">
      <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center shrink-0">
        <Brain className="w-3.5 h-3.5 text-brand-500" />
      </div>
      <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-brand-300 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function FindPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<HomefinderResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const isDone = result !== null;

  // Auto-scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading || isDone) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // Send only role + content (strip thought)
      const payload = next.map(({ role, content }) => ({ role, content }));
      const response = await chatHomeFinder(payload);

      if (response.action === "question") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: response.question, thought: response.thought },
        ]);
      } else {
        // Results — show a closing message then the result panel
        const n = response.result.matched_listings.length;
        const summary =
          n > 0
            ? `I found ${n} listing${n !== 1 ? "s" : ""} that match what you're looking for! Here's what I understood about your needs, and why these properties fit.`
            : `I searched based on everything you've told me, but didn't find exact matches in the current listings. Here's my full reasoning — you may want to broaden your criteria.`;
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: summary, thought: response.thought },
        ]);
        setResult(response.result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleReset() {
    setMessages([INITIAL_MESSAGE]);
    setInput("");
    setResult(null);
    setError(null);
    setTimeout(() => inputRef.current?.focus(), 50);
  }

  const exchangeCount = messages.filter((m) => m.role === "user").length;

  return (
    <div className="max-w-3xl mx-auto py-8 px-6 flex flex-col gap-6">
      {/* Header */}
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-bold text-gray-900">Find your perfect home</h1>
        <p className="text-sm text-gray-500">
          Tell me what you&apos;re looking for — I&apos;ll ask a few questions, then find matching listings and explain my reasoning.
        </p>
      </div>

      {/* Chat area */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-1 min-h-[320px] max-h-[480px]">
          {messages.map((msg, i) =>
            msg.role === "assistant" ? (
              <div key={i} className="flex items-end gap-2 mb-4">
                <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center shrink-0 mb-auto mt-1">
                  <Brain className="w-3.5 h-3.5 text-brand-500" />
                </div>
                <div className="max-w-[80%]">
                  <div className="bg-gray-50 border border-gray-100 text-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed shadow-sm">
                    {msg.content}
                  </div>
                  {msg.thought && <ThoughtBubble thought={msg.thought} />}
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-end mb-4">
                <div className="max-w-[75%] bg-brand-500 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed shadow-sm">
                  {msg.content}
                </div>
              </div>
            )
          )}

          {loading && <TypingIndicator />}
          <div ref={chatEndRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-gray-100 px-4 py-3 flex items-end gap-3 bg-white">
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || isDone}
            placeholder={isDone ? "Search complete — start over to search again" : "Type your reply… (Enter to send, Shift+Enter for new line)"}
            className="flex-1 resize-none rounded-xl border border-gray-200 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 outline-none text-sm px-3.5 py-2.5 text-gray-800 placeholder-gray-400 transition-all disabled:bg-gray-50 disabled:text-gray-400 leading-relaxed"
            style={{ maxHeight: "120px" }}
            autoFocus
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim() || isDone}
            className="shrink-0 w-9 h-9 rounded-xl bg-brand-500 text-white flex items-center justify-center hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Reset + progress hint */}
      <div className="flex items-center justify-between text-xs text-gray-400">
        {exchangeCount > 0 ? (
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 hover:text-brand-500 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Start over
          </button>
        ) : (
          <span />
        )}
        {!isDone && exchangeCount > 0 && (
          <span>{exchangeCount < 4 ? `${4 - exchangeCount} or fewer questions remaining` : "Searching soon…"}</span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 px-5 py-4 text-sm">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {result && <HomeFinderResults result={result} />}
    </div>
  );
}

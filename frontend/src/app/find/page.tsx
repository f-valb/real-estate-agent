"use client";

import { useState } from "react";
import { Search, Loader2, Sparkles } from "lucide-react";
import { findHomes } from "@/lib/api";
import type { HomefinderResult } from "@/lib/types";
import HomeFinderResults from "@/components/HomeFinderResults";

const EXAMPLES = [
  "3-bed family home near good schools in Austin, yard is a must, budget around $500k",
  "Modern condo downtown with 2 beds, under $400k, walkable neighbourhood",
  "Quiet suburban house with 4 bedrooms, large lot, under $700k",
];

export default function FindPage() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<HomefinderResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await findHomes(description.trim());
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto py-10 px-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 bg-brand-50 text-brand-600 text-sm font-medium px-4 py-1.5 rounded-full border border-brand-200 mb-3">
          <Sparkles className="w-3.5 h-3.5" />
          AI-powered home search
        </div>
        <h1 className="text-3xl font-bold text-gray-900">Find your perfect home</h1>
        <p className="text-gray-500 max-w-xl mx-auto">
          Describe what you&apos;re looking for in plain language. Our AI will understand your needs,
          search real listings, and explain exactly why each result matches.
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700 block mb-2">
            Describe your dream home
          </span>
          <textarea
            className="w-full rounded-xl border border-gray-200 focus:border-brand-400 focus:ring-2 focus:ring-brand-100 outline-none resize-none text-gray-800 placeholder-gray-400 text-sm px-4 py-3 transition-all"
            rows={4}
            placeholder="e.g. 3-bed family home near good schools in Austin, yard is a must, budget around $500k…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={loading}
          />
        </label>

        {/* Example chips */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-gray-400 self-center mr-1">Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setDescription(ex)}
              className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-500 hover:border-brand-300 hover:text-brand-600 hover:bg-brand-50 transition-colors"
              disabled={loading}
            >
              {ex.length > 55 ? ex.slice(0, 52) + "…" : ex}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={loading || !description.trim()}
          className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-brand-500 text-white font-medium hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              AI is searching listings…
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Search with AI
            </>
          )}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 px-5 py-4 text-sm">
          <strong>Search failed:</strong> {error}
        </div>
      )}

      {/* Results */}
      {result && <HomeFinderResults result={result} />}
    </div>
  );
}

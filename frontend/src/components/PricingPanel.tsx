"use client";

import { useState } from "react";
import { analyzePrice } from "@/lib/api";
import type { PricingRecommendation } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import { Sparkles, TrendingUp, AlertCircle, Loader2 } from "lucide-react";

interface Props {
  propertyId: string;
}

export default function PricingPanel({ propertyId }: Props) {
  const [result, setResult] = useState<PricingRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await analyzePrice(propertyId);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-indigo-600" />
        </div>
        <h2 className="font-semibold text-gray-900">AI Pricing Analysis</h2>
      </div>

      {!result && !loading && (
        <div className="text-center py-8">
          <p className="text-gray-500 text-sm mb-4">
            Get a market-based price recommendation powered by AI. The agent will pull comparable sales and market statistics to justify a recommended list price.
          </p>
          <button
            onClick={run}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            Get AI Pricing Analysis
          </button>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          <p className="text-sm text-gray-500">Agent is analyzing comps and market data…</p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 rounded-xl text-red-700 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
          <button onClick={run} className="ml-auto underline text-xs">Retry</button>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Recommended price */}
          <div className="text-center py-4 bg-indigo-50 rounded-xl">
            <p className="text-xs text-indigo-500 font-medium uppercase tracking-wide mb-1">Recommended Price</p>
            <p className="text-4xl font-bold text-indigo-700">
              ${result.recommended_price.toLocaleString()}
            </p>
            <div className="mt-2">
              <StatusBadge value={result.confidence} variant="confidence" />
              <span className="text-xs text-indigo-400 ml-2">confidence</span>
            </div>
          </div>

          {/* Price range bar */}
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Low: ${result.price_range_low.toLocaleString()}</span>
              <span>High: ${result.price_range_high.toLocaleString()}</span>
            </div>
            <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="absolute top-0 h-full bg-indigo-400 rounded-full"
                style={{
                  left: "0%",
                  right: "0%",
                }}
              />
              {/* Marker for recommended price */}
              {(() => {
                const range = result.price_range_high - result.price_range_low;
                const pct = range > 0
                  ? ((result.recommended_price - result.price_range_low) / range) * 100
                  : 50;
                return (
                  <div
                    className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-indigo-600 rounded-full shadow"
                    style={{ left: `calc(${pct}% - 6px)` }}
                  />
                );
              })()}
            </div>
          </div>

          {/* Comps */}
          {result.market_context.total_comps_found > 0 && (
            <div className="text-sm text-gray-500">
              Based on <span className="font-medium text-gray-700">{result.market_context.total_comps_found}</span> comparable sales
              {result.market_context.median_price && (
                <> · Median area price: <span className="font-medium text-gray-700">${Math.round(result.market_context.median_price).toLocaleString()}</span></>
              )}
            </div>
          )}

          {/* Justification */}
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Agent Reasoning</p>
            <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-xl">{result.justification}</p>
          </div>

          <button
            onClick={run}
            className="w-full py-2 text-xs text-indigo-500 hover:text-indigo-700 transition-colors"
          >
            Re-run analysis
          </button>
        </div>
      )}
    </div>
  );
}

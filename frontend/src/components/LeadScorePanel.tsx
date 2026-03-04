"use client";

import { useState } from "react";
import { scoreLead } from "@/lib/api";
import type { LeadAssessment } from "@/lib/types";
import { Brain, AlertCircle, Loader2, Clock, CheckCircle } from "lucide-react";

const ACTION_LABELS: Record<string, string> = {
  call: "📞 Call",
  email: "✉️ Email",
  send_listings: "🏠 Send Listings",
  schedule_showing: "📅 Schedule Showing",
  refer_to_lender: "🏦 Refer to Lender",
  nurture: "🌱 Nurture",
  archive: "📦 Archive",
};

const QUAL_STYLES = {
  hot: { ring: "text-red-500", bg: "bg-red-50", badge: "bg-red-100 text-red-700", emoji: "🔥" },
  warm: { ring: "text-amber-500", bg: "bg-amber-50", badge: "bg-amber-100 text-amber-700", emoji: "☀️" },
  cold: { ring: "text-slate-400", bg: "bg-slate-50", badge: "bg-slate-100 text-slate-600", emoji: "❄️" },
};

interface Props {
  contactId: string;
}

export default function LeadScorePanel({ contactId }: Props) {
  const [result, setResult] = useState<LeadAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await scoreLead(contactId);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  };

  const style = result ? QUAL_STYLES[result.qualification] : null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-violet-50 rounded-lg flex items-center justify-center">
          <Brain className="w-4 h-4 text-violet-600" />
        </div>
        <h2 className="font-semibold text-gray-900">AI Lead Scoring</h2>
      </div>

      {!result && !loading && (
        <div className="text-center py-8">
          <p className="text-gray-500 text-sm mb-4">
            Score this lead with AI. The agent analyses engagement history, pipeline stage, preferences, and market activity to produce a 0–100 score with recommended next actions.
          </p>
          <button
            onClick={run}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-violet-600 text-white rounded-xl text-sm font-medium hover:bg-violet-700 transition-colors"
          >
            <Brain className="w-4 h-4" />
            Score This Lead
          </button>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
          <p className="text-sm text-gray-500">Agent is evaluating lead quality…</p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 rounded-xl text-red-700 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
          <button onClick={run} className="ml-auto underline text-xs">Retry</button>
        </div>
      )}

      {result && style && (
        <div className="space-y-5">
          {/* Score ring + qualification */}
          <div className={`flex items-center gap-4 p-4 ${style.bg} rounded-xl`}>
            <div className="relative w-20 h-20 shrink-0">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="34" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                <circle
                  cx="40" cy="40" r="34" fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  strokeDasharray={`${2 * Math.PI * 34}`}
                  strokeDashoffset={`${2 * Math.PI * 34 * (1 - result.lead_score / 100)}`}
                  strokeLinecap="round"
                  className={style.ring}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xl font-bold text-gray-900">{result.lead_score}</span>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{style.emoji}</span>
                <span className={`text-sm font-bold uppercase tracking-wide px-2.5 py-0.5 rounded-full ${style.badge}`}>
                  {result.qualification}
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-sm text-gray-600">
                <Clock className="w-3.5 h-3.5 text-gray-400" />
                {result.buying_timeline}
              </div>
              {result.matching_listing_count > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  {result.matching_listing_count} matching listing{result.matching_listing_count !== 1 ? "s" : ""}
                </p>
              )}
            </div>
          </div>

          {/* Recommended actions */}
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Recommended Actions</p>
            <div className="flex flex-wrap gap-2">
              {result.recommended_actions.map((action) => (
                <span
                  key={action}
                  className="flex items-center gap-1 text-xs px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg font-medium"
                >
                  <CheckCircle className="w-3 h-3" />
                  {ACTION_LABELS[action] ?? action}
                </span>
              ))}
            </div>
          </div>

          {/* Reasoning */}
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Agent Reasoning</p>
            <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-xl">{result.reasoning}</p>
          </div>

          <button
            onClick={run}
            className="w-full py-2 text-xs text-violet-500 hover:text-violet-700 transition-colors"
          >
            Re-run scoring
          </button>
        </div>
      )}
    </div>
  );
}

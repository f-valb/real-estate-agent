import type { HomefinderResult } from "@/lib/types";
import PropertyCard from "./PropertyCard";
import { MapPin, DollarSign, BedDouble, Sparkles, Brain, CheckCircle2 } from "lucide-react";

interface Props {
  result: HomefinderResult;
}

function fmt(n: number | null): string | null {
  if (n == null) return null;
  return n >= 1000 ? `$${(n / 1000).toFixed(0)}k` : `$${n}`;
}

export default function HomeFinderResults({ result }: Props) {
  const c = result.extracted_criteria;

  const chips: { icon: React.ReactNode; label: string }[] = [];
  if (c.location) chips.push({ icon: <MapPin className="w-3.5 h-3.5" />, label: c.location });
  if (c.min_price != null || c.max_price != null) {
    const lo = fmt(c.min_price);
    const hi = fmt(c.max_price);
    const label = lo && hi ? `${lo} – ${hi}` : lo ? `≥ ${lo}` : `≤ ${hi!}`;
    chips.push({ icon: <DollarSign className="w-3.5 h-3.5" />, label });
  }
  if (c.min_bedrooms != null)
    chips.push({ icon: <BedDouble className="w-3.5 h-3.5" />, label: `${c.min_bedrooms}+ bedrooms` });
  if (c.property_type)
    chips.push({ icon: <CheckCircle2 className="w-3.5 h-3.5" />, label: c.property_type.replace(/_/g, " ") });
  for (const p of c.priorities)
    chips.push({ icon: <Sparkles className="w-3.5 h-3.5" />, label: p });

  return (
    <div className="space-y-8">
      {/* Understanding panel */}
      <div className="bg-white rounded-2xl border border-brand-100 shadow-sm overflow-hidden">
        <div className="bg-brand-50 px-6 py-4 border-b border-brand-100 flex items-center gap-2">
          <Brain className="w-5 h-5 text-brand-500" />
          <h2 className="font-semibold text-brand-800 text-sm">What the AI understood</h2>
        </div>
        <div className="px-6 py-5 space-y-4">
          {/* Buyer intent */}
          <p className="text-gray-800 font-medium text-base leading-relaxed border-l-4 border-brand-400 pl-4 italic">
            &ldquo;{result.buyer_intent}&rdquo;
          </p>

          {/* Criteria chips */}
          {chips.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {chips.map((chip, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-xs font-medium"
                >
                  {chip.icon}
                  {chip.label}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Reasoning panel */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-700 text-sm">Agent reasoning</h2>
          <span className="text-xs text-gray-400 bg-white border border-gray-200 rounded-full px-2.5 py-0.5">
            {result.total_found} listing{result.total_found !== 1 ? "s" : ""} matched
          </span>
        </div>
        <div className="px-6 py-5">
          <p className="text-gray-700 text-sm leading-relaxed">{result.match_reasoning}</p>
        </div>
      </div>

      {/* Matched listings */}
      {result.matched_listings.length > 0 ? (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Matched listings
            <span className="ml-2 text-sm font-normal text-gray-400">ranked best-first</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {result.matched_listings.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400 bg-white rounded-2xl border border-gray-100">
          <Building2Icon className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="font-medium">No matching listings found</p>
          <p className="text-sm mt-1">Try broadening your search criteria</p>
        </div>
      )}
    </div>
  );
}

// Inline icon to avoid additional import just for the empty state
function Building2Icon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15l.75 3.75H3.75L4.5 3zM3.75 6.75h16.5v14.25H3.75V6.75zM9 11.25v3.75m6-3.75v3.75M9 6.75V3M15 6.75V3" />
    </svg>
  );
}

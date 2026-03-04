import Link from "next/link";
import type { PropertyResponse } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import { BedDouble, Bath, Maximize2, ArrowRight } from "lucide-react";

interface Props {
  property: PropertyResponse;
}

const TYPE_LABELS: Record<string, string> = {
  single_family: "Single Family",
  condo: "Condo",
  townhouse: "Townhouse",
  multi_family: "Multi-Family",
  land: "Land",
};

export default function PropertyCard({ property: p }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow flex flex-col">
      {/* Colored header band based on status */}
      <div className={`h-2 w-full ${p.status === "active" ? "bg-green-400" : p.status === "pending" ? "bg-yellow-400" : p.status === "sold" ? "bg-gray-400" : "bg-indigo-300"}`} />

      <div className="p-5 flex flex-col flex-1">
        <div className="flex items-start justify-between mb-2">
          <StatusBadge value={p.status} variant="listing" />
          <span className="text-xs text-gray-400">{TYPE_LABELS[p.property_type] ?? p.property_type}</span>
        </div>

        <p className="text-2xl font-bold text-gray-900 mt-2">
          ${Number(p.list_price).toLocaleString()}
        </p>
        <p className="text-sm font-medium text-gray-700 mt-0.5">{p.address_line1}</p>
        <p className="text-sm text-gray-500">{p.city}, {p.state} {p.zip_code}</p>

        <div className="flex items-center gap-4 mt-3 text-gray-500 text-sm">
          {p.bedrooms != null && (
            <span className="flex items-center gap-1">
              <BedDouble className="w-3.5 h-3.5" /> {p.bedrooms} bd
            </span>
          )}
          {p.bathrooms != null && (
            <span className="flex items-center gap-1">
              <Bath className="w-3.5 h-3.5" /> {p.bathrooms} ba
            </span>
          )}
          {p.square_feet != null && (
            <span className="flex items-center gap-1">
              <Maximize2 className="w-3.5 h-3.5" /> {p.square_feet.toLocaleString()} sqft
            </span>
          )}
        </div>

        <div className="mt-auto pt-4">
          <Link
            href={`/listings/${p.id}`}
            className="flex items-center justify-center gap-2 w-full py-2 rounded-xl bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition-colors"
          >
            Analyze Price <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

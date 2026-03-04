import { getListing } from "@/lib/api";
import PricingPanel from "@/components/PricingPanel";
import StatusBadge from "@/components/StatusBadge";
import { BedDouble, Bath, Maximize2, Calendar, MapPin, Hash } from "lucide-react";
import Link from "next/link";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ListingDetailPage({ params }: Props) {
  const { id } = await params;
  const p = await getListing(id);

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-6">
        <Link href="/listings" className="text-sm text-brand-600 hover:underline mb-3 inline-block">← Back to listings</Link>
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold text-gray-900">{p.address_line1}</h1>
          <StatusBadge value={p.status} variant="listing" />
        </div>
        <p className="text-gray-500 mt-1">{p.city}, {p.state} {p.zip_code}</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Property details */}
        <div className="xl:col-span-3 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <p className="text-3xl font-bold text-gray-900 mb-4">${Number(p.list_price).toLocaleString()}</p>

            <div className="grid grid-cols-3 gap-4 py-4 border-y border-gray-100">
              {p.bedrooms != null && (
                <div className="text-center">
                  <BedDouble className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                  <p className="font-semibold text-gray-900">{p.bedrooms}</p>
                  <p className="text-xs text-gray-500">Bedrooms</p>
                </div>
              )}
              {p.bathrooms != null && (
                <div className="text-center">
                  <Bath className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                  <p className="font-semibold text-gray-900">{p.bathrooms}</p>
                  <p className="text-xs text-gray-500">Bathrooms</p>
                </div>
              )}
              {p.square_feet != null && (
                <div className="text-center">
                  <Maximize2 className="w-5 h-5 text-gray-400 mx-auto mb-1" />
                  <p className="font-semibold text-gray-900">{p.square_feet.toLocaleString()}</p>
                  <p className="text-xs text-gray-500">Sq Ft</p>
                </div>
              )}
            </div>

            <div className="mt-4 space-y-2 text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                <span>{p.address_line1}{p.address_line2 ? `, ${p.address_line2}` : ""}, {p.city}, {p.state} {p.zip_code}</span>
              </div>
              {p.year_built && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="w-4 h-4 text-gray-400 shrink-0" />
                  <span>Built in {p.year_built}</span>
                </div>
              )}
              {p.mls_number && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Hash className="w-4 h-4 text-gray-400 shrink-0" />
                  <span>MLS# {p.mls_number}</span>
                </div>
              )}
            </div>

            {p.description && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-sm text-gray-600 leading-relaxed">{p.description}</p>
              </div>
            )}
          </div>
        </div>

        {/* AI Pricing Panel */}
        <div className="xl:col-span-2">
          <PricingPanel propertyId={p.id} />
        </div>
      </div>
    </div>
  );
}

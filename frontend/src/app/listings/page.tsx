import { getListings } from "@/lib/api";
import PropertyCard from "@/components/PropertyCard";

export default async function ListingsPage() {
  const data = await getListings({ limit: "50" });

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Property Listings</h1>
        <p className="text-gray-500 text-sm mt-1">{data.total} properties · Click any card to get an AI pricing analysis</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {data.items.map((p) => (
          <PropertyCard key={p.id} property={p} />
        ))}
      </div>
    </div>
  );
}

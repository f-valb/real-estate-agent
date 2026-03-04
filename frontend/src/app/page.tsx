import { getListings, getContacts } from "@/lib/api";
import { Building2, Users, TrendingUp, Flame } from "lucide-react";
import Link from "next/link";

export default async function Dashboard() {
  const [listings, contacts] = await Promise.all([
    getListings({ limit: "100" }),
    getContacts({ limit: "100" }),
  ]);

  const activeListings = listings.items.filter((l) => l.status === "active").length;
  const hotLeads = contacts.items.filter((c) => c.pipeline_stage === "qualified" || c.pipeline_stage === "proposal" || c.pipeline_stage === "negotiation").length;

  const stats = [
    { label: "Total Listings", value: listings.total, icon: Building2, color: "text-indigo-600", bg: "bg-indigo-50", href: "/listings" },
    { label: "Active Listings", value: activeListings, icon: TrendingUp, color: "text-green-600", bg: "bg-green-50", href: "/listings" },
    { label: "Total Contacts", value: contacts.total, icon: Users, color: "text-blue-600", bg: "bg-blue-50", href: "/contacts" },
    { label: "Engaged Leads", value: hotLeads, icon: Flame, color: "text-orange-600", bg: "bg-orange-50", href: "/contacts" },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">AI-powered real estate overview</p>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-10">
        {stats.map(({ label, value, icon: Icon, color, bg, href }) => (
          <Link
            key={label}
            href={href}
            className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
          >
            <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center mb-3`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <p className="text-3xl font-bold text-gray-900">{value}</p>
            <p className="text-sm text-gray-500 mt-0.5">{label}</p>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Listings */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Recent Listings</h2>
            <Link href="/listings" className="text-sm text-brand-600 hover:underline">View all →</Link>
          </div>
          <div className="space-y-3">
            {listings.items.slice(0, 5).map((l) => (
              <Link
                key={l.id}
                href={`/listings/${l.id}`}
                className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0 hover:bg-gray-50 px-2 -mx-2 rounded-lg transition-colors"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{l.address_line1}</p>
                  <p className="text-xs text-gray-500">{l.city}, {l.state}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">${Number(l.list_price).toLocaleString()}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${l.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                    {l.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Contacts */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Recent Contacts</h2>
            <Link href="/contacts" className="text-sm text-brand-600 hover:underline">View all →</Link>
          </div>
          <div className="space-y-3">
            {contacts.items.slice(0, 5).map((c) => (
              <Link
                key={c.id}
                href={`/contacts/${c.id}`}
                className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0 hover:bg-gray-50 px-2 -mx-2 rounded-lg transition-colors"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{c.first_name} {c.last_name}</p>
                  <p className="text-xs text-gray-500 capitalize">{c.contact_type}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${
                  c.pipeline_stage === "new" ? "bg-sky-100 text-sky-700" :
                  c.pipeline_stage === "contacted" ? "bg-blue-100 text-blue-700" :
                  c.pipeline_stage === "qualified" ? "bg-violet-100 text-violet-700" :
                  "bg-gray-100 text-gray-600"
                }`}>
                  {c.pipeline_stage.replace("_", " ")}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

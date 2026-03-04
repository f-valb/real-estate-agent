import { getContact } from "@/lib/api";
import LeadScorePanel from "@/components/LeadScorePanel";
import StatusBadge from "@/components/StatusBadge";
import { Mail, Phone, Building2, MapPin, Tag } from "lucide-react";
import Link from "next/link";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ContactDetailPage({ params }: Props) {
  const { id } = await params;
  const c = await getContact(id);

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-6">
        <Link href="/contacts" className="text-sm text-brand-600 hover:underline mb-3 inline-block">← Back to contacts</Link>
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold text-gray-900">{c.first_name} {c.last_name}</h1>
          <StatusBadge value={c.contact_type} variant="contact" />
          <StatusBadge value={c.pipeline_stage} variant="pipeline" />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Contact details */}
        <div className="xl:col-span-3 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Contact Info</h2>
            <div className="space-y-3 text-sm">
              {c.email && (
                <div className="flex items-center gap-2 text-gray-700">
                  <Mail className="w-4 h-4 text-gray-400 shrink-0" />
                  <a href={`mailto:${c.email}`} className="hover:text-indigo-600">{c.email}</a>
                </div>
              )}
              {c.phone && (
                <div className="flex items-center gap-2 text-gray-700">
                  <Phone className="w-4 h-4 text-gray-400 shrink-0" />
                  {c.phone}
                </div>
              )}
              {c.company && (
                <div className="flex items-center gap-2 text-gray-700">
                  <Building2 className="w-4 h-4 text-gray-400 shrink-0" />
                  {c.company}
                </div>
              )}
              {c.lead_source && (
                <div className="flex items-center gap-2 text-gray-700">
                  <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                  Source: {c.lead_source}
                </div>
              )}
              {c.tags.length > 0 && (
                <div className="flex items-start gap-2 text-gray-700">
                  <Tag className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                  <div className="flex gap-1.5 flex-wrap">
                    {c.tags.map((t) => (
                      <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{t}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {c.preferences && Object.keys(c.preferences).length > 0 && (
              <div className="mt-5 pt-4 border-t border-gray-100">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Preferences</h3>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(c.preferences).map(([k, v]) => (
                    <div key={k} className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg">
                      <span className="font-medium capitalize">{k.replace(/_/g, " ")}:</span>{" "}
                      {typeof v === "number" && k.includes("price") ? `$${Number(v).toLocaleString()}` : String(v)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {c.notes && (
              <div className="mt-5 pt-4 border-t border-gray-100">
                <h3 className="text-sm font-medium text-gray-700 mb-1">Notes</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{c.notes}</p>
              </div>
            )}
          </div>
        </div>

        {/* AI Lead Scoring Panel */}
        <div className="xl:col-span-2">
          <LeadScorePanel contactId={c.id} />
        </div>
      </div>
    </div>
  );
}

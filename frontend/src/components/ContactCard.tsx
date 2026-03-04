import Link from "next/link";
import type { ContactResponse } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import { Mail, Phone, ArrowRight } from "lucide-react";

interface Props {
  contact: ContactResponse;
}

export default function ContactCard({ contact: c }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow flex flex-col gap-2">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-semibold text-gray-900">{c.first_name} {c.last_name}</p>
        </div>
        <div className="flex gap-1.5">
          <StatusBadge value={c.contact_type} variant="contact" />
          <StatusBadge value={c.pipeline_stage} variant="pipeline" />
        </div>
      </div>
      {c.email && (
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Mail className="w-3 h-3" /> {c.email}
        </div>
      )}
      {c.phone && (
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Phone className="w-3 h-3" /> {c.phone}
        </div>
      )}
      <div className="mt-1">
        <Link
          href={`/contacts/${c.id}`}
          className="flex items-center justify-center gap-1.5 w-full py-1.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-medium hover:bg-indigo-100 transition-colors"
        >
          Score Lead <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}

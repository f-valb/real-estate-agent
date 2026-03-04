interface Props {
  value: string;
  variant?: "listing" | "pipeline" | "contact" | "qualification" | "confidence";
}

const LISTING_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  sold: "bg-gray-100 text-gray-700",
  draft: "bg-slate-100 text-slate-600",
  withdrawn: "bg-red-100 text-red-700",
};

const PIPELINE_COLORS: Record<string, string> = {
  new: "bg-sky-100 text-sky-800",
  contacted: "bg-blue-100 text-blue-800",
  qualified: "bg-violet-100 text-violet-800",
  proposal: "bg-orange-100 text-orange-800",
  negotiation: "bg-amber-100 text-amber-800",
  closed_won: "bg-green-100 text-green-800",
  closed_lost: "bg-red-100 text-red-700",
};

const CONTACT_COLORS: Record<string, string> = {
  buyer: "bg-indigo-100 text-indigo-800",
  seller: "bg-emerald-100 text-emerald-800",
  lead: "bg-sky-100 text-sky-800",
  agent: "bg-purple-100 text-purple-800",
  vendor: "bg-gray-100 text-gray-700",
};

const QUALIFICATION_COLORS: Record<string, string> = {
  hot: "bg-red-100 text-red-700",
  warm: "bg-amber-100 text-amber-800",
  cold: "bg-slate-100 text-slate-600",
};

const CONFIDENCE_COLORS: Record<string, string> = {
  high: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-gray-100 text-gray-600",
};

export default function StatusBadge({ value, variant = "listing" }: Props) {
  const maps = {
    listing: LISTING_COLORS,
    pipeline: PIPELINE_COLORS,
    contact: CONTACT_COLORS,
    qualification: QUALIFICATION_COLORS,
    confidence: CONFIDENCE_COLORS,
  };
  const colors = maps[variant][value] ?? "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${colors}`}
    >
      {value.replace(/_/g, " ")}
    </span>
  );
}

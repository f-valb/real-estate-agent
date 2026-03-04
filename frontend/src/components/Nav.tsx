"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Building2, Users, Search } from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/listings", label: "Listings", icon: Building2 },
  { href: "/contacts", label: "Contacts", icon: Users },
  { href: "/find", label: "Find a Home", icon: Search },
];

export default function Nav() {
  const path = usePathname();
  return (
    <aside className="w-56 shrink-0 bg-white border-r border-gray-200 flex flex-col min-h-screen">
      <div className="px-6 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-brand-500 flex items-center justify-center">
            <Building2 className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-gray-900 text-sm">RE Agent</span>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {links.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? path === "/" : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-brand-50 text-brand-600"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-6 py-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">Powered by Qwen2.5 · Ollama</p>
      </div>
    </aside>
  );
}

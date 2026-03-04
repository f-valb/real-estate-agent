import { getContacts } from "@/lib/api";
import ContactCard from "@/components/ContactCard";

export default async function ContactsPage() {
  const data = await getContacts({ limit: "100" });

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">CRM Contacts</h1>
        <p className="text-gray-500 text-sm mt-1">{data.total} contacts · Click any card to score with AI</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {data.items.map((c) => (
          <ContactCard key={c.id} contact={c} />
        ))}
      </div>
    </div>
  );
}

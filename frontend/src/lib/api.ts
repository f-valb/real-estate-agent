const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8090";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

import type {
  ListingsPage,
  PropertyResponse,
  ContactsPage,
  ContactResponse,
  PricingRecommendation,
  LeadAssessment,
  HomefinderResult,
} from "./types";

export const getListings = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchJSON<ListingsPage>(`/api/v1/listings${qs}`);
};

export const getListing = (id: string) =>
  fetchJSON<PropertyResponse>(`/api/v1/listings/${id}`);

export const getContacts = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchJSON<ContactsPage>(`/api/v1/contacts${qs}`);
};

export const getContact = (id: string) =>
  fetchJSON<ContactResponse>(`/api/v1/contacts/${id}`);

export const analyzePrice = (property_id: string) =>
  fetchJSON<PricingRecommendation>("/api/v1/agents/pricing/analyze", {
    method: "POST",
    body: JSON.stringify({ property_id }),
  });

export const scoreLead = (contact_id: string) =>
  fetchJSON<LeadAssessment>("/api/v1/agents/leads/score", {
    method: "POST",
    body: JSON.stringify({ contact_id }),
  });

export const findHomes = (description: string) =>
  fetchJSON<HomefinderResult>("/api/v1/agents/home-finder/search", {
    method: "POST",
    body: JSON.stringify({ description }),
  });

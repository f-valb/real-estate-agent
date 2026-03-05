export interface PropertyResponse {
  id: string;
  mls_number: string | null;
  status: string;
  property_type: string;
  address_line1: string;
  address_line2: string | null;
  city: string;
  state: string;
  zip_code: string;
  list_price: number;
  bedrooms: number | null;
  bathrooms: number | null;
  square_feet: number | null;
  lot_size_sqft: number | null;
  year_built: number | null;
  description: string | null;
  listing_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface ListingsPage {
  items: PropertyResponse[];
  total: number;
  page: number;
  limit: number;
}

export interface ContactResponse {
  id: string;
  contact_type: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  company: string | null;
  pipeline_stage: string;
  lead_source: string | null;
  notes: string | null;
  preferences: Record<string, unknown> | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ContactsPage {
  items: ContactResponse[];
  total: number;
  page: number;
  limit: number;
}

export interface MarketContext {
  median_price: number | null;
  avg_dom: number | null;
  total_comps_found: number;
}

export interface PricingRecommendation {
  recommended_price: number;
  price_range_low: number;
  price_range_high: number;
  confidence: "low" | "medium" | "high";
  justification: string;
  comps_used: string[];
  market_context: MarketContext;
}

export interface LeadAssessment {
  lead_score: number;
  qualification: "hot" | "warm" | "cold";
  buying_timeline: string;
  recommended_actions: string[];
  reasoning: string;
  matching_listing_count: number;
}

export interface ExtractedCriteria {
  location: string | null;
  min_price: number | null;
  max_price: number | null;
  min_bedrooms: number | null;
  property_type: string | null;
  priorities: string[];
}

export interface HomefinderResult {
  buyer_intent: string;
  extracted_criteria: ExtractedCriteria;
  match_reasoning: string;
  matched_listing_ids: string[];
  total_found: number;
  matched_listings: PropertyResponse[];
  search_params_used: Record<string, unknown>;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  thought?: string;
}

export type ChatStepResponse =
  | { action: "question"; thought: string; question: string }
  | { action: "results"; thought: string; result: HomefinderResult };

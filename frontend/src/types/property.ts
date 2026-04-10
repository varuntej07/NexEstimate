// TypeScript interfaces matching the backend Pydantic models

export interface ZestimateRange {
  low_percent: string | null;
  high_percent: string | null;
}

export interface PropertyEstimate {
  // Core estimate
  zestimate: number | null;
  zestimate_range: ZestimateRange | null;
  rent_zestimate: number | null;

  // Address
  street_address: string | null;
  city: string | null;
  state: string | null;
  zipcode: string | null;
  full_address: string | null;
  county: string | null;

  // Property details
  bedrooms: number | null;
  bathrooms: number | null;
  living_area: number | null;
  lot_size: number | null;
  year_built: number | null;
  home_type: string | null;
  home_status: string | null;
  property_tax_rate: number | null;

  // Pricing
  price: number | null;
  last_sold_price: number | null;
  days_on_zillow: number | null;

  // Media
  image_url: string | null;
  street_view_url: string | null;
  zillow_url: string | null;

  // Description
  description: string | null;

  // Metadata
  zpid: number | null;
  page_view_count: number | null;
  favorite_count: number | null;
}

export interface ApiError {
  detail: string;
}

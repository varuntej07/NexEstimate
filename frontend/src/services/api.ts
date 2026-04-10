import type { PropertyEstimate, ApiError } from "../types/property";

const API_BASE = "/api";

// Fetch property estimate from the backend API. Throws an error with a user-friendly message on failure
export async function fetchEstimate(address: string): Promise<PropertyEstimate> {
  const params = new URLSearchParams({ address });
  const response = await fetch(`${API_BASE}/estimate?${params}`);

  if (!response.ok) {
    const body: ApiError = await response.json().catch(() => ({
      detail: `Server error (${response.status})`,
    }));
    throw new Error(body.detail);
  }

  return response.json();
}

// Format a number as US currency (e.g. 1158800 -> "$1,158,800")
export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

// Format a number with commas (e.g. 2680 -> "2,680")
export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("en-US").format(value);
}

// Format home type from API format (e.g. "SINGLE_FAMILY" -> "Single Family")
export function formatHomeType(value: string | null | undefined): string {
  if (!value) return "N/A";
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

// Format home status (e.g. "FOR_SALE" -> "For Sale")
export function formatHomeStatus(value: string | null | undefined): string {
  if (!value) return "N/A";
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

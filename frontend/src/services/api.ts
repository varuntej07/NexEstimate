import type { PropertyEstimate, ApiError, UiError } from "../types/property";

const API_BASE = "/api";

function classifyError(status: number, message: string): UiError {
  if (status === 422) return { title: "Invalid address", message: "Please enter a valid US address starting with a street number and try again.", retryable: false };
  if (status === 404) return { title: "Address not found", message, retryable: false };
  if (status === 429) return { title: "Too many requests", message, retryable: true };
  return { title: "Something went wrong", message, retryable: true };
}

// Fetch property estimate from the backend API.
export async function fetchEstimate(address: string): Promise<PropertyEstimate> {
  const params = new URLSearchParams({ address });

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/estimate?${params}`);
  } catch {
    const err = new Error("Could not reach the server. Check your connection.");
    (err as Error & { uiError: UiError }).uiError = {
      title: "Connection failed",
      message: "Could not reach the server. Check your connection.",
      retryable: true,
    };
    throw err;
  }

  if (!response.ok) {
    // slowapi returns { "error": "..." }, FastAPI returns { "detail": "..." } or { "detail": [...] }
    const body: ApiError & { error?: string } = await response.json().catch(() => ({}));
    const raw = body.detail ?? body.error;
    const message =
      typeof raw === "string"
        ? raw
        : Array.isArray(raw) && raw.length > 0
          ? raw[0]?.msg ?? `Server error (${response.status})`
          : `Server error (${response.status})`;
    const uiError = classifyError(response.status, message);
    const err = new Error(message);
    (err as Error & { uiError: UiError }).uiError = uiError;
    throw err;
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

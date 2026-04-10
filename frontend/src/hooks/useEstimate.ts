import { useState, useCallback } from "react";
import type { PropertyEstimate } from "../types/property";
import { fetchEstimate } from "../services/api";

interface UseEstimateReturn {
  data: PropertyEstimate | null;
  loading: boolean;
  error: string | null;
  search: (address: string) => Promise<void>;
  reset: () => void;
}

/**
 * Custom hook for fetching property estimates.
 * Encapsulates loading/error/data state management.
 */
export function useEstimate(): UseEstimateReturn {
  const [data, setData] = useState<PropertyEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (address: string) => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const result = await fetchEstimate(address);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, search, reset };
}

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../contexts/AuthContext.new";
import { propertyService } from "../services/PropertyService";
import type { Property } from "../types/property";

interface UsePropertiesResult {
  properties: Property[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useProperties(): UsePropertiesResult {
  const { user, isLoading } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchingRef = useRef(false);

  const fetchProperties = useCallback(async () => {
    if (isLoading || !user || fetchingRef.current) return;

    try {
      fetchingRef.current = true;
      setLoading(true);
      setError(null);

      const tenantId =
        user.tenant_id ||
        user.app_metadata?.tenant_id ||
        user.user_metadata?.tenant_id;

      const data = await propertyService.getProperties({
        userId: user.id,
        tenantId,
      });

      setProperties(data);
    } catch (err: any) {
      console.error("Failed to fetch properties:", err);
      setError(err.message || "Failed to load properties");
      setProperties([]);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
    }
  }, [user, isLoading]);

  useEffect(() => {
    fetchProperties();
  }, [fetchProperties]);

  return {
    properties,
    loading,
    error,
    refetch: async () => {
      propertyService.clearCache();
      await fetchProperties();
    },
  };
}

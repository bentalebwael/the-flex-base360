/**
 * Property Service - Single Source of Truth for Properties
 */

import type { Property } from "../types/property";

export class PropertyError extends Error {
  constructor(
    public code: "MISSING_TENANT" | "FETCH_FAILED" | "NETWORK_ERROR",
    message: string,
    public details?: any,
  ) {
    super(message);
    this.name = "PropertyError";
  }
}

interface PropertyContext {
  userId: string;
  tenantId?: string;
}

export class PropertyService {
  private static instance: PropertyService;
  private properties: Property[] = [];
  private currentTenantId: string | null = null;
  private fetchPromise: Promise<Property[]> | null = null;
  private lastFetchTime: number = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  private constructor() {}

  static getInstance(): PropertyService {
    if (!PropertyService.instance) {
      PropertyService.instance = new PropertyService();
    }
    return PropertyService.instance;
  }

  async getProperties(context: PropertyContext): Promise<Property[]> {
    try {
      // Relaxed check: We allow missing tenantId and let backend handle auth
      // if (!context.tenantId) {
      //   throw new PropertyError(
      //     "MISSING_TENANT",
      //     "Cannot fetch properties without tenant context",
      //   );
      // }

      if (
        context.tenantId &&
        this.currentTenantId &&
        this.currentTenantId !== context.tenantId
      ) {
        this.clearCache();
      }

      if (this.fetchPromise) {
        return await this.fetchPromise;
      }

      if (this.isCacheValid(context.tenantId)) {
        return this.properties;
      }

      this.fetchPromise = this.fetchPropertiesFromAPI(context);

      try {
        this.properties = await this.fetchPromise;
        if (context.tenantId) {
          this.currentTenantId = context.tenantId;
        }
        this.lastFetchTime = Date.now();
        return this.properties;
      } finally {
        this.fetchPromise = null;
      }
    } catch (error) {
      throw error;
    }
  }

  private async fetchPropertiesFromAPI(
    context: PropertyContext,
  ): Promise<Property[]> {
    try {
      const token = await this.getAccessToken();
      if (!token) {
        throw new PropertyError(
          "NETWORK_ERROR",
          "No authentication token available",
        );
      }

      const backend = import.meta.env.VITE_BACKEND_URL || "";
      const url = `${backend}/api/v1/dashboard/properties`;

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new PropertyError(
          "FETCH_FAILED",
          `Failed to fetch properties: ${response.statusText}`,
        );
      }

      const data = await response.json();
      return data.properties || [];
    } catch (error) {
      if (error instanceof PropertyError) throw error;
      throw new PropertyError(
        "NETWORK_ERROR",
        error instanceof Error ? error.message : "Unknown error",
        error,
      );
    }
  }

  private async getAccessToken(): Promise<string | null> {
    try {
      const { supabase } = await import("../lib/supabase");
      const {
        data: { session },
      } = await supabase.auth.getSession();
      return session?.access_token || null;
    } catch (error) {
      console.error("[PropertyService] Failed to get access token:", error);
      return null;
    }
  }

  private isCacheValid(tenantId?: string): boolean {
    if (this.properties.length === 0) return false;
    if (tenantId && this.currentTenantId !== tenantId) return false;
    if (Date.now() - this.lastFetchTime > this.CACHE_DURATION) return false;
    return true;
  }

  clearCache(): void {
    this.properties = [];
    this.currentTenantId = null;
    this.fetchPromise = null;
    this.lastFetchTime = 0;
  }
}

export const propertyService = PropertyService.getInstance();

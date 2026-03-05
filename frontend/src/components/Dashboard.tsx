import React, { useEffect, useState } from "react";
import { RevenueSummary } from "./RevenueSummary";
import { SecureAPI } from "../lib/secureApi";

interface DashboardProperty {
  id: string;
  name: string;
  timezone?: string;
}

const Dashboard: React.FC = () => {
  const [properties, setProperties] = useState<DashboardProperty[]>([]);
  const [selectedProperty, setSelectedProperty] = useState("");
  const [isLoadingProperties, setIsLoadingProperties] = useState(true);
  const [propertiesError, setPropertiesError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadProperties = async () => {
      setIsLoadingProperties(true);
      setPropertiesError("");

      try {
        const result = await SecureAPI.getDashboardProperties();
        const propertyList = Array.isArray(result) ? result : [];
        if (cancelled) return;

        setProperties(propertyList);

        if (propertyList.length === 0) {
          setSelectedProperty("");
          return;
        }

        setSelectedProperty((previousSelection) => {
          if (propertyList.some((property) => property.id === previousSelection)) {
            return previousSelection;
          }
          return propertyList[0].id;
        });
      } catch (error) {
        if (cancelled) return;
        setProperties([]);
        setSelectedProperty("");
        setPropertiesError("Failed to load properties");
        console.error("Failed to fetch dashboard properties:", error);
      } finally {
        if (!cancelled) {
          setIsLoadingProperties(false);
        }
      }
    };

    loadProperties();

    return () => {
      cancelled = true;
    };
  }, []);

  const hasProperties = properties.length > 0;

  return (
    <div className="p-4 lg:p-6 min-h-full">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">Property Management Dashboard</h1>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 lg:p-6">
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
              <div>
                <h2 className="text-lg lg:text-xl font-medium text-gray-900 mb-2">Revenue Overview</h2>
                <p className="text-sm lg:text-base text-gray-600">
                  Monthly performance insights for your properties
                </p>
              </div>
              
              {/* Property Selector */}
              <div className="flex flex-col sm:items-end">
                <label className="text-xs font-medium text-gray-700 mb-1">Select Property</label>
                <select
                  value={selectedProperty}
                  onChange={(e) => setSelectedProperty(e.target.value)}
                  disabled={isLoadingProperties || !hasProperties}
                  className="block w-full sm:w-auto min-w-[200px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  {isLoadingProperties && (
                    <option value="">Loading properties...</option>
                  )}
                  {!isLoadingProperties && !hasProperties && (
                    <option value="">No properties available</option>
                  )}
                  {!isLoadingProperties && properties.map((property) => (
                    <option key={property.id} value={property.id}>
                      {property.name}
                    </option>
                  ))}
                </select>
                {propertiesError && (
                  <p className="mt-2 text-xs text-red-600">{propertiesError}</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {selectedProperty ? (
              <RevenueSummary propertyId={selectedProperty} />
            ) : (
              <div className="text-sm text-gray-500">No property selected.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

import React, { useEffect, useState } from "react";
import { RevenueSummary } from "./RevenueSummary";
import { SecureAPI } from "../lib/secureApi";

interface DashboardProperty {
  id: string;
  name: string;
  timezone: string;
}

const Dashboard: React.FC = () => {
  const [properties, setProperties] = useState<DashboardProperty[]>([]);
  const [selectedProperty, setSelectedProperty] = useState("");
  const [loadingProperties, setLoadingProperties] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    const loadProperties = async () => {
      setLoadingProperties(true);
      setError("");

      try {
        const response = await SecureAPI.getDashboardProperties();
        if (!isMounted) {
          return;
        }

        const tenantProperties = response.properties ?? [];
        setProperties(tenantProperties);
        setSelectedProperty((currentSelection) => {
          if (tenantProperties.some((property) => property.id === currentSelection)) {
            return currentSelection;
          }
          return tenantProperties[0]?.id ?? "";
        });
      } catch (loadError) {
        if (!isMounted) {
          return;
        }

        console.error(loadError);
        setError("Failed to load your properties.");
      } finally {
        if (isMounted) {
          setLoadingProperties(false);
        }
      }
    };

    loadProperties();

    return () => {
      isMounted = false;
    };
  }, []);

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
                  Revenue totals for the properties in your account
                </p>
              </div>
              
              {/* Property Selector */}
              <div className="flex flex-col sm:items-end">
                <label className="text-xs font-medium text-gray-700 mb-1">Select Property</label>
                <select
                  value={selectedProperty}
                  onChange={(e) => setSelectedProperty(e.target.value)}
                  disabled={loadingProperties || properties.length === 0}
                  className="block w-full sm:w-auto min-w-[200px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  {properties.map((property) => (
                    <option key={property.id} value={property.id}>
                      {property.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {error && (
              <div className="p-4 text-red-500 bg-red-50 rounded-lg">{error}</div>
            )}
            {!error && loadingProperties && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
                Loading your properties...
              </div>
            )}
            {!error && !loadingProperties && properties.length === 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
                No properties are available for this account.
              </div>
            )}
            {!error && !loadingProperties && properties.length > 0 && (
              <RevenueSummary propertyId={selectedProperty} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

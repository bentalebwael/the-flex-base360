import React, { useState, useMemo, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext.new";
import { RevenueSummary } from "./RevenueSummary";

const PROPERTIES_BY_TENANT: { tenant_id: string; id: string; name: string }[] = [
  { tenant_id: 'tenant-a', id: 'prop-001', name: 'Beach House Alpha' },
  { tenant_id: 'tenant-a', id: 'prop-002', name: 'City Apartment Downtown' },
  { tenant_id: 'tenant-a', id: 'prop-003', name: 'Country Villa Estate' },
  { tenant_id: 'tenant-b', id: 'prop-001', name: 'Mountain Lodge Beta' },
  { tenant_id: 'tenant-b', id: 'prop-004', name: 'Lakeside Cottage' },
  { tenant_id: 'tenant-b', id: 'prop-005', name: 'Urban Loft Modern' },
];

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const tenantId =
    user?.tenant_id ??
    user?.app_metadata?.tenant_id ??
    (user as any)?.user_metadata?.tenant_id ??
    null;
  const properties = useMemo(() => {
    if (!tenantId) return [];
    return PROPERTIES_BY_TENANT.filter((p) => p.tenant_id === tenantId);
  }, [tenantId]);
  const firstPropertyId = properties[0]?.id ?? '';
  const [selectedProperty, setSelectedProperty] = useState(firstPropertyId);

  useEffect(() => {
    if (!properties.length) return;
    const validSelection = properties.some((p) => p.id === selectedProperty);
    if (!validSelection || !selectedProperty) {
      setSelectedProperty(properties[0].id);
    }
  }, [properties, selectedProperty]);

  const isLoadingProperties = !tenantId || properties.length === 0;

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
                  value={selectedProperty || firstPropertyId}
                  onChange={(e) => setSelectedProperty(e.target.value)}
                  disabled={isLoadingProperties}
                  className="block w-full sm:w-auto min-w-[200px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  {isLoadingProperties ? (
                    <option value="">Loading properties...</option>
                  ) : (
                    properties.map((property) => (
                      <option key={property.id} value={property.id}>
                        {property.name}
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {(selectedProperty || firstPropertyId) ? (
              <RevenueSummary propertyId={selectedProperty || firstPropertyId} />
            ) : (
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 text-gray-500 text-sm">
                Loading...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

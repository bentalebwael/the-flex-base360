import React, { useCallback, useEffect, useState } from "react";
import { RevenueSummary } from "./RevenueSummary";
import { SecureAPI } from "../lib/secureApi";

interface DashboardProperty {
  id: string;
  name: string;
  timezone?: string;
}

const MONTH_OPTIONS = [
  { value: 1, label: "January" },
  { value: 2, label: "February" },
  { value: 3, label: "March" },
  { value: 4, label: "April" },
  { value: 5, label: "May" },
  { value: 6, label: "June" },
  { value: 7, label: "July" },
  { value: 8, label: "August" },
  { value: 9, label: "September" },
  { value: 10, label: "October" },
  { value: 11, label: "November" },
  { value: 12, label: "December" },
];

const CURRENT_MONTH = new Date().getMonth() + 1;
const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 10 }, (_, index) => CURRENT_YEAR - index);

const Dashboard: React.FC = () => {
  const [properties, setProperties] = useState<DashboardProperty[]>([]);
  const [selectedProperty, setSelectedProperty] = useState("");
  const [selectedMonth, setSelectedMonth] = useState<number | undefined>(undefined);
  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined);
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
  const disableFilters = isLoadingProperties || !hasProperties;

  const handleMonthChange = useCallback((value: string) => {
    if (!value) {
      setSelectedMonth(undefined);
      setSelectedYear(undefined);
      return;
    }
    setSelectedMonth(Number(value));
    setSelectedYear((current) => current ?? CURRENT_YEAR);
  }, []);

  const handleYearChange = useCallback((value: string) => {
    if (!value) {
      setSelectedYear(undefined);
      setSelectedMonth(undefined);
      return;
    }
    setSelectedYear(Number(value));
    setSelectedMonth((current) => current ?? CURRENT_MONTH);
  }, []);

  const handleReportPeriodResolved = useCallback((month: number, year: number) => {
    setSelectedMonth((current) => current ?? month);
    setSelectedYear((current) => current ?? year);
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
                  Monthly performance insights for your properties
                </p>
              </div>
              
              {/* Property Selector */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full sm:w-auto">
                <div className="flex flex-col">
                  <label className="text-xs font-medium text-gray-700 mb-1">Select Property</label>
                  <select
                    value={selectedProperty}
                    onChange={(e) => setSelectedProperty(e.target.value)}
                    disabled={disableFilters}
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
                </div>
                <div className="flex flex-col">
                  <label className="text-xs font-medium text-gray-700 mb-1">Month</label>
                  <select
                    value={selectedMonth ?? ""}
                    onChange={(e) => handleMonthChange(e.target.value)}
                    disabled={disableFilters}
                    className="block w-full sm:w-auto min-w-[150px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                  >
                    <option value="">Latest</option>
                    {MONTH_OPTIONS.map((month) => (
                      <option key={month.value} value={month.value}>
                        {month.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col">
                  <label className="text-xs font-medium text-gray-700 mb-1">Year</label>
                  <select
                    value={selectedYear ?? ""}
                    onChange={(e) => handleYearChange(e.target.value)}
                    disabled={disableFilters}
                    className="block w-full sm:w-auto min-w-[120px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                  >
                    <option value="">Latest</option>
                    {YEAR_OPTIONS.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
                {propertiesError && (
                  <p className="text-xs text-red-600 sm:col-span-3">{propertiesError}</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {selectedProperty ? (
              <RevenueSummary
                propertyId={selectedProperty}
                month={selectedMonth}
                year={selectedYear}
                onReportPeriodResolved={handleReportPeriodResolved}
              />
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

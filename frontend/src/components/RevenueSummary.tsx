import React, { useEffect, useState } from 'react';
import { SecureAPI } from '../lib/secureApi';

interface RevenueData {
    property_id: string;
    total_revenue: string;
    total_revenue_all_time: string;
    previous_month_revenue?: string;
    revenue_change_percent?: string | null;
    revenue_trend_direction?: "up" | "down" | "flat" | null;
    currency: string;
    reservations_count: number;
    report_month?: number | null;
    report_year?: number | null;
    property_timezone?: string | null;
}

interface RevenueSummaryProps {
    propertyId?: string;
    month?: number;
    year?: number;
    onReportPeriodResolved?: (month: number, year: number) => void;
    showRaw?: boolean;
}

const MONTH_LABELS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
];

export const RevenueSummary: React.FC<RevenueSummaryProps> = ({
    propertyId = 'prop-001',
    month,
    year,
    onReportPeriodResolved,
    showRaw,
}) => {
    const [data, setData] = useState<RevenueData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchRevenue = async () => {
            setLoading(true);
            try {
                const response = await SecureAPI.getDashboardSummary(propertyId, {
                    month,
                    year,
                    timestamp: Date.now()
                });
                setData(response);
                if (
                    onReportPeriodResolved &&
                    typeof response?.report_month === "number" &&
                    typeof response?.report_year === "number"
                ) {
                    onReportPeriodResolved(response.report_month, response.report_year);
                }
            } catch (err) {
                setError('Failed to load revenue data');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchRevenue();
    }, [propertyId, month, year, onReportPeriodResolved]);

    if (loading) {
        return (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="animate-pulse space-y-4">
                    <div className="h-4 bg-gray-100 rounded w-1/4"></div>
                    <div className="h-8 bg-gray-100 rounded w-1/2"></div>
                    <div className="flex gap-4 pt-4">
                        <div className="h-12 bg-gray-100 rounded flex-1"></div>
                        <div className="h-12 bg-gray-100 rounded flex-1"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) return <div className="p-4 text-red-500 bg-red-50 rounded-lg">{error}</div>;
    if (!data) return null;

    const formatAmount = (amount: string): string => {
        const safe = (amount || "0").trim();
        const sign = safe.startsWith("-") ? "-" : "";
        const unsigned = safe.replace(/^[+-]/, "");
        const [rawWhole = "0", rawFraction = ""] = unsigned.split(".");
        const whole = (rawWhole.replace(/\D/g, "") || "0");
        const fraction = (rawFraction.replace(/\D/g, "") + "00").slice(0, 2);
        const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return `${sign}${grouped}.${fraction}`;
    };

    const hasSubCentPrecision = (() => {
        const fraction = (data.total_revenue || "").split(".")[1];
        return !!fraction && fraction.length > 2;
    })();

    const periodLabel = (() => {
        if (typeof data.report_month === "number" && typeof data.report_year === "number") {
            const monthName = MONTH_LABELS[data.report_month - 1] || `Month ${data.report_month}`;
            return `${monthName} ${data.report_year}`;
        }
        return "Latest month";
    })();

    const trendBadge = (() => {
        const direction =
            data.revenue_trend_direction === "up" ||
            data.revenue_trend_direction === "down" ||
            data.revenue_trend_direction === "flat"
                ? data.revenue_trend_direction
                : "flat";

        const parsedPercent = (() => {
            if (typeof data.revenue_change_percent !== "string") {
                return null;
            }
            const value = Number(data.revenue_change_percent);
            return Number.isFinite(value) ? value : null;
        })();

        const label =
            parsedPercent === null
                ? (direction === "up" ? "New" : direction === "down" ? "N/A" : "0.00%")
                : `${Math.abs(parsedPercent).toFixed(2)}%`;

        if (direction === "down") {
            return {
                label,
                containerClass: "bg-red-100 text-red-800",
                iconClass: "text-red-500",
                iconPath:
                    "M14.707 10.293a1 1 0 00-1.414 0L11 12.586V5a1 1 0 10-2 0v7.586L6.707 10.293a1 1 0 10-1.414 1.414l4 4a1 1 0 001.414 0l4-4a1 1 0 000-1.414z",
            };
        }

        if (direction === "flat") {
            return {
                label,
                containerClass: "bg-gray-100 text-gray-700",
                iconClass: "text-gray-500",
                iconPath: "M5 10a1 1 0 100 2h10a1 1 0 100-2H5z",
            };
        }

        return {
            label,
            containerClass: "bg-green-100 text-green-800",
            iconClass: "text-green-500",
            iconPath:
                "M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z",
        };
    })();

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow duration-300">
            {showRaw && (
                <div className="p-3 bg-gray-50 text-xs font-mono border-b border-gray-100 overflow-auto max-h-32">
                    <strong className="block mb-1 text-gray-500 uppercase tracking-wider text-[10px]">Raw API Response</strong>
                    <pre className="text-gray-700">{JSON.stringify(data, null, 2)}</pre>
                </div>
            )}

            <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Revenue ({periodLabel})</h2>
                        <div className="flex items-baseline gap-2 mt-1">
                            <span className="text-3xl font-bold text-gray-900 tracking-tight">
                                {data.currency} {formatAmount(data.total_revenue)}
                            </span>
                            <span
                                className={`inline-flex items-baseline px-2.5 py-0.5 rounded-full text-xs font-medium md:mt-2 lg:mt-0 ${trendBadge.containerClass}`}
                                title="Compared with previous month"
                            >
                                <svg
                                    className={`-ml-1 mr-0.5 h-3 w-3 flex-shrink-0 self-center ${trendBadge.iconClass}`}
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                    aria-hidden="true"
                                >
                                    <path fillRule="evenodd" d={trendBadge.iconPath} clipRule="evenodd" />
                                </svg>
                                {trendBadge.label}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                    <div>
                        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Property ID</p>
                        <p className="text-sm font-semibold text-gray-700 font-mono mt-1">{data.property_id}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Reservations</p>
                        <p className="text-sm font-semibold text-gray-700 mt-1">{data.reservations_count} <span className="font-normal text-gray-400">bookings</span></p>
                    </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Total Revenue (All Time)</p>
                    <p className="text-xl font-semibold text-gray-900 mt-1">
                        {data.currency} {formatAmount(data.total_revenue_all_time || "0")}
                    </p>
                    {data.property_timezone && (
                        <p className="text-xs text-gray-500 mt-1">
                            Reporting timezone: {data.property_timezone}
                        </p>
                    )}
                </div>

                {/* Precision Warning Area */}
                <div className="mt-4 h-6">
                    {hasSubCentPrecision && showRaw && (
                        <div className="flex items-center text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                            <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            Precision Mismatch Detected
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

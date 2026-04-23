// frontend/src/components/RevenueSummary.tsx:60-65 — Bug 2 (frontend rounding)


    if (error) return <div className="p-4 text-red-500 bg-red-50 rounded-lg">{error}</div>;
    if (!data) return null;

    const displayTotal = Math.round(data.total_revenue * 100) / 100;


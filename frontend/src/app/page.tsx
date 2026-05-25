"use client";

import { useEffect, useState } from "react";
import { fetchSummary, fetchCosts, triggerScan } from "@/lib/api";
import SummaryCards from "@/components/SummaryCards";
import CostChart from "@/components/CostChart";
import TopServicesChart from "@/components/TopServicesChart";

interface SummaryData {
  total_monthly_spend: number;
  month_over_month_change: number;
  total_potential_savings: number;
  resources_scanned: number;
  last_scan_time: string | null;
  top_services: { service: string; total: number }[];
}

export default function Dashboard() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [costs, setCosts] = useState([]);
  const [scanning, setScanning] = useState(false);

  const loadData = async () => {
    const [s, c] = await Promise.all([fetchSummary(), fetchCosts()]);
    setSummary(s);
    setCosts(c);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    await triggerScan();
    await loadData();
    setScanning(false);
  };

  const hasData = summary && summary.last_scan_time;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          {summary?.last_scan_time && (
            <p className="text-sm text-gray-400 mt-1">
              Last scanned: {new Date(summary.last_scan_time).toLocaleString()}
            </p>
          )}
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors cursor-pointer disabled:cursor-not-allowed"
        >
          {scanning ? "Scanning..." : "Scan Now"}
        </button>
      </div>

      {!hasData ? (
        <div className="flex flex-col items-center justify-center h-96 bg-gray-900 border border-gray-800 rounded-xl">
          <p className="text-xl text-gray-400 mb-4">No scan data yet</p>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 text-white px-8 py-3 rounded-lg font-medium text-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            {scanning ? "Scanning..." : "Run Your First Scan"}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <SummaryCards data={summary} />
          <CostChart data={costs} />
          <TopServicesChart data={summary.top_services} />
        </div>
      )}
    </div>
  );
}

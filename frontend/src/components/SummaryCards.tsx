"use client";

interface SummaryData {
  total_monthly_spend: number;
  month_over_month_change: number;
  total_potential_savings: number;
  resources_scanned: number;
  last_scan_time: string | null;
}

export default function SummaryCards({ data }: { data: SummaryData | null }) {
  if (!data) return null;

  const cards = [
    {
      label: "Monthly Spend",
      value: `$${data.total_monthly_spend.toLocaleString()}`,
      color: "text-white",
    },
    {
      label: "Month-over-Month",
      value: `${data.month_over_month_change > 0 ? "+" : ""}${data.month_over_month_change}%`,
      color: data.month_over_month_change > 0 ? "text-red-400" : "text-emerald-400",
    },
    {
      label: "Potential Savings",
      value: `$${data.total_potential_savings.toLocaleString()}`,
      color: "text-emerald-400",
    },
    {
      label: "Resources Scanned",
      value: data.resources_scanned.toString(),
      color: "text-white",
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-gray-900 border border-gray-800 rounded-xl p-6"
        >
          <p className="text-sm text-gray-400 mb-1">{card.label}</p>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}

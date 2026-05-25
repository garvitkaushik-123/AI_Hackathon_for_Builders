"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface CostEntry {
  service: string;
  date: string;
  amount: number;
}

const COLORS: Record<string, string> = {
  ec2: "#10b981",
  rds: "#3b82f6",
  s3: "#f59e0b",
  ebs: "#8b5cf6",
};

export default function CostChart({ data }: { data: CostEntry[] }) {
  const grouped: Record<string, Record<string, number>> = {};
  for (const entry of data) {
    if (!grouped[entry.date]) grouped[entry.date] = {};
    grouped[entry.date][entry.service] = (grouped[entry.date][entry.service] || 0) + entry.amount;
  }

  const chartData = Object.entries(grouped)
    .map(([date, services]) => ({
      date: date.slice(5),
      ...services,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));

  const services = [...new Set(data.map((d) => d.service))];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Cost Trend (30 days)</h2>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `$${v}`} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "8px" }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(value) => [`$${Number(value).toFixed(2)}`, ""]}
          />
          <Legend />
          {services.map((service) => (
            <Area
              key={service}
              type="monotone"
              dataKey={service}
              stackId="1"
              fill={COLORS[service] || "#6b7280"}
              stroke={COLORS[service] || "#6b7280"}
              fillOpacity={0.6}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

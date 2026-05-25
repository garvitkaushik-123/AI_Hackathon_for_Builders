"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface ServiceTotal {
  service: string;
  total: number;
}

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"];

export default function TopServicesChart({ data }: { data: ServiceTotal[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Top Services by Spend</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical">
          <XAxis type="number" stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `$${v}`} />
          <YAxis
            type="category"
            dataKey="service"
            stroke="#9ca3af"
            fontSize={12}
            width={50}
            tickFormatter={(v) => v.toUpperCase()}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "8px" }}
            formatter={(value) => [`$${Number(value).toFixed(2)}`, "Spend"]}
          />
          <Bar dataKey="total" radius={[0, 6, 6, 0]}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

"use client";

interface Recommendation {
  id: number;
  resource_id: string | null;
  severity: string;
  title: string;
  description: string;
  estimated_savings: number;
  status: string;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-900/30 border-red-800 text-red-400",
  warning: "bg-yellow-900/30 border-yellow-800 text-yellow-400",
  info: "bg-blue-900/30 border-blue-800 text-blue-400",
};

const BADGE_STYLES: Record<string, string> = {
  critical: "bg-red-600",
  warning: "bg-yellow-600",
  info: "bg-blue-600",
};

export default function RecommendationCard({
  rec,
  onDismiss,
}: {
  rec: Recommendation;
  onDismiss: (id: number) => void;
}) {
  if (rec.status === "dismissed") return null;

  return (
    <div className={`border rounded-lg p-4 ${SEVERITY_STYLES[rec.severity] || ""}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full text-white ${BADGE_STYLES[rec.severity]}`}>
            {rec.severity}
          </span>
          <span className="text-emerald-400 font-medium text-sm">
            Save ${rec.estimated_savings}/mo
          </span>
        </div>
        <button
          onClick={() => onDismiss(rec.id)}
          className="text-gray-500 hover:text-gray-300 text-xs cursor-pointer"
        >
          Dismiss
        </button>
      </div>
      <h3 className="font-medium text-sm text-white mb-1">{rec.title}</h3>
      <p className="text-xs text-gray-400">{rec.description}</p>
      {rec.resource_id && (
        <p className="text-xs text-gray-500 mt-2 font-mono">{rec.resource_id}</p>
      )}
    </div>
  );
}

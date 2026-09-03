import React from "react";

interface StatusBadgeProps {
  type: "severity" | "status" | "scan_type";
  value: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value }) => {
  const v = (value || "").toUpperCase();

  if (type === "severity") {
    const config: Record<string, { bg: string; text: string; border: string }> = {
      CRITICAL: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
      HIGH: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
      MEDIUM: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
      LOW: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
      INFO: { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200" },
    };
    const c = config[v] || config.INFO;
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${c.bg} ${c.text} ${c.border}`}>
        {v}
      </span>
    );
  }

  if (type === "status") {
    const config: Record<string, { bg: string; text: string; dot: string }> = {
      COMPLETED: { bg: "bg-emerald-50 text-emerald-700", text: "Completed", dot: "bg-emerald-500" },
      RUNNING: { bg: "bg-blue-50 text-blue-700", text: "Running", dot: "bg-blue-500 animate-ping" },
      FAILED: { bg: "bg-red-50 text-red-700", text: "Failed", dot: "bg-red-500" },
      CANCELLED: { bg: "bg-slate-100 text-slate-700", text: "Cancelled", dot: "bg-slate-400" },
      PENDING: { bg: "bg-amber-50 text-amber-700", text: "Pending", dot: "bg-amber-400" },
      OPEN: { bg: "bg-rose-50 text-rose-700", text: "Open", dot: "bg-rose-500" },
      ACKNOWLEDGED: { bg: "bg-amber-50 text-amber-700", text: "Acknowledged", dot: "bg-amber-500" },
      FIXED: { bg: "bg-emerald-50 text-emerald-700", text: "Fixed", dot: "bg-emerald-500" },
      IGNORED: { bg: "bg-slate-100 text-slate-600", text: "Ignored", dot: "bg-slate-400" },
      REGRESSION: { bg: "bg-purple-50 text-purple-700", text: "Regression", dot: "bg-purple-600 animate-pulse" },
    };
    const c = config[v] || { bg: "bg-slate-50 text-slate-700", text: v, dot: "bg-slate-400" };
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
        {c.text}
      </span>
    );
  }

  return (
    <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
      {value}
    </span>
  );
};

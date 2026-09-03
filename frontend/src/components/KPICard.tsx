import React from "react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  variant?: "default" | "critical" | "high" | "warning" | "success";
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon,
  variant = "default",
}) => {
  const variantStyles = {
    default: "text-slate-900",
    critical: "text-red-600",
    high: "text-orange-600",
    warning: "text-amber-600",
    success: "text-emerald-600",
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-xs transition hover:shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        <div className="p-2 bg-slate-50 rounded-lg text-slate-600 border border-slate-100">{icon}</div>
      </div>
      <div className="mt-3">
        <div className={`text-2xl font-bold tracking-tight ${variantStyles[variant]}`}>
          {value}
        </div>
        {subtitle && (
          <p className="mt-1 text-xs text-slate-500 flex items-center gap-1">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};

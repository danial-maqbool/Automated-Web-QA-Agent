import React from "react";
import { QARun, Issue, Project, PageRecord } from "../api/types";
import { KPICard } from "../components/KPICard";
import { StatusBadge } from "../components/StatusBadge";
import {
  ShieldAlert,
  FileCheck,
  AlertOctagon,
  Accessibility,
  WifiOff,
  Activity,
  ArrowRight,
  TrendingDown,
  Clock,
  Sparkles
} from "lucide-react";

interface DashboardProps {
  currentProject: Project | null;
  latestRun: QARun | null;
  recentRuns: QARun[];
  issues: Issue[];
  pages: PageRecord[];
  onNavigateToIssues: () => void;
  onNavigateToRuns: () => void;
  onNavigateToPages: () => void;
  onRunDemo: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  currentProject,
  latestRun,
  recentRuns,
  issues,
  pages,
  onNavigateToIssues,
  onNavigateToRuns,
  onNavigateToPages,
  onRunDemo,
}) => {
  const score = latestRun?.qa_score ?? 100.0;
  const criticalCount = issues.filter((i) => i.severity === "CRITICAL").length;
  const highCount = issues.filter((i) => i.severity === "HIGH").length;
  const a11yCount = issues.filter((i) => i.category === "Accessibility").length;

  // Categories breakdown
  const categoryCounts: Record<string, number> = {};
  for (const i of issues) {
    categoryCounts[i.category] = (categoryCounts[i.category] || 0) + 1;
  }

  // Regression issues
  const regressions = issues.filter((i) => i.status === "REGRESSION");

  return (
    <div className="space-y-6">
      {/* Welcome Banner if no runs yet */}
      {!latestRun && (
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-xl p-6 shadow-sm flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Welcome to WebQA Agent</h2>
            <p className="text-blue-100 text-sm mt-1 max-w-xl">
              Inspect websites autonomously, detect functional defects, verify accessibility (WCAG),
              check responsive layouts, and validate visual regressions without external AI dependencies.
            </p>
          </div>
          <button
            onClick={onRunDemo}
            className="flex items-center gap-2 bg-white text-blue-700 px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-50 transition shadow-sm cursor-pointer shrink-0"
          >
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span>Launch Benchmark Demo</span>
          </button>
        </div>
      )}

      {/* Top KPI Cards (Req 54) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <KPICard
          title="WebQA Score"
          value={`${score}/100`}
          subtitle={score >= 85 ? "Good Health" : "Needs Attention"}
          icon={<Activity className="w-5 h-5 text-blue-600" />}
          variant={score >= 85 ? "success" : "critical"}
        />
        <KPICard
          title="Pages Tested"
          value={latestRun?.pages_tested ?? pages.length}
          subtitle="Discovered routes"
          icon={<FileCheck className="w-5 h-5 text-emerald-600" />}
        />
        <KPICard
          title="Total Issues"
          value={issues.length}
          subtitle="Deduplicated defects"
          icon={<ShieldAlert className="w-5 h-5 text-amber-600" />}
          variant={issues.length > 0 ? "warning" : "success"}
        />
        <KPICard
          title="Critical / High"
          value={criticalCount + highCount}
          subtitle={`${criticalCount} Critical, ${highCount} High`}
          icon={<AlertOctagon className="w-5 h-5 text-red-600" />}
          variant={criticalCount > 0 ? "critical" : highCount > 0 ? "high" : "default"}
        />
        <KPICard
          title="Accessibility"
          value={a11yCount}
          subtitle="WCAG 2.1 AA Violations"
          icon={<Accessibility className="w-5 h-5 text-purple-600" />}
        />
        <KPICard
          title="Regressions"
          value={regressions.length}
          subtitle="Drift from baseline"
          icon={<TrendingDown className="w-5 h-5 text-rose-600" />}
          variant={regressions.length > 0 ? "critical" : "default"}
        />
      </div>

      {/* Grid: Issue Severity & Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h3 className="font-semibold text-slate-900 text-sm mb-4">Issue Severity Distribution</h3>
          <div className="space-y-3">
            {[
              { label: "Critical", count: criticalCount, color: "bg-red-500", text: "text-red-700" },
              { label: "High", count: highCount, color: "bg-orange-500", text: "text-orange-700" },
              {
                label: "Medium",
                count: issues.filter((i) => i.severity === "MEDIUM").length,
                color: "bg-amber-500",
                text: "text-amber-700",
              },
              {
                label: "Low",
                count: issues.filter((i) => i.severity === "LOW").length,
                color: "bg-blue-500",
                text: "text-blue-700",
              },
            ].map((s) => {
              const pct = issues.length > 0 ? Math.round((s.count / issues.length) * 100) : 0;
              return (
                <div key={s.label}>
                  <div className="flex justify-between text-xs font-medium text-slate-600 mb-1">
                    <span>{s.label}</span>
                    <span className="font-bold">{s.count} ({pct}%)</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${s.color}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 text-sm">Defects by Quality Category</h3>
            <button
              onClick={onNavigateToIssues}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>View all issues</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          {Object.keys(categoryCounts).length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-xs">
              No defects recorded. Run a scan to populate findings.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {Object.entries(categoryCounts).map(([cat, count]) => (
                <div key={cat} className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
                  <div className="text-xs text-slate-500 font-medium truncate">{cat}</div>
                  <div className="text-lg font-bold text-slate-800 mt-1">{count}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent QA Runs & Top Failing Pages */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent QA Runs */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 text-sm">Recent QA Runs</h3>
            <button
              onClick={onNavigateToRuns}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>All runs</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {recentRuns.slice(0, 5).map((r) => (
              <div key={r.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <StatusBadge type="status" value={r.status} />
                    <span className="text-xs font-semibold text-slate-800">{r.scan_type}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(r.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-slate-900">{r.qa_score}/100</div>
                  <div className="text-[11px] text-slate-500">{r.total_issues} issues</div>
                </div>
              </div>
            ))}
            {recentRuns.length === 0 && (
              <p className="text-xs text-slate-400 text-center py-6">No runs recorded yet.</p>
            )}
          </div>
        </div>

        {/* Discovered Pages Preview */}
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 text-sm">Discovered Pages Inventory</h3>
            <button
              onClick={onNavigateToPages}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
            >
              <span>Explore all pages</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {pages.slice(0, 5).map((p) => (
              <div key={p.id} className="py-3 flex items-center justify-between">
                <div className="truncate max-w-xs">
                  <span className="text-xs font-medium text-slate-900 block truncate">{p.path}</span>
                  <span className="text-[11px] text-slate-400 truncate block">{p.title || "No title"}</span>
                </div>
                <div className="text-right flex items-center gap-2">
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                      p.status_code === 200 ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                    }`}
                  >
                    {p.status_code || "N/A"}
                  </span>
                  <span className="text-xs text-slate-500">{p.load_time_ms ? `${Math.round(p.load_time_ms)}ms` : ""}</span>
                </div>
              </div>
            ))}
            {pages.length === 0 && (
              <p className="text-xs text-slate-400 text-center py-6">No pages discovered yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

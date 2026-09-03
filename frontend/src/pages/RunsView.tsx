import React from "react";
import { QARun } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { PlayCircle, Clock, Eye, AlertCircle } from "lucide-react";

interface RunsViewProps {
  runs: QARun[];
  onSelectRun: (runId: string) => void;
}

export const RunsView: React.FC<RunsViewProps> = ({ runs, onSelectRun }) => {
  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-blue-600" />
            <span>QA Execution Runs History</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Audit history, scan telemetry, quality scores, and regression trends across all browser sessions.
          </p>
        </div>
        <div className="text-xs font-semibold text-slate-500">
          Total Executions: <span className="font-bold text-slate-900">{runs.length}</span>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold uppercase text-slate-500 tracking-wider">
              <tr>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Scan Type</th>
                <th className="py-3 px-4">Browser & Viewport</th>
                <th className="py-3 px-4">Pages</th>
                <th className="py-3 px-4">WebQA Score</th>
                <th className="py-3 px-4">Total Issues</th>
                <th className="py-3 px-4">Started At</th>
                <th className="py-3 px-4 text-right">Telemetry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => onSelectRun(r.id)}
                  className="hover:bg-slate-50/80 transition cursor-pointer"
                >
                  <td className="py-3 px-4 whitespace-nowrap">
                    <StatusBadge type="status" value={r.status} />
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-900 whitespace-nowrap">
                    {r.scan_type}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap font-mono text-[11px] text-slate-500 capitalize">
                    {r.browser} ({r.viewport_width}x{r.viewport_height})
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap font-mono text-slate-600">
                    {r.pages_tested} / {r.pages_discovered}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap font-bold text-blue-600">
                    {r.qa_score}/100
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="font-bold text-red-600">{r.total_issues}</span>
                    <span className="text-slate-400 text-[11px]"> ({r.critical_issues} Crit)</span>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRun(r.id);
                      }}
                      className="p-1 rounded text-blue-600 hover:bg-blue-50 transition"
                      title="View Telemetry"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No runs executed yet. Trigger a scan from the top bar.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

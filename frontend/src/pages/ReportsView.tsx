import React from "react";
import { QARun } from "../api/types";
import { BarChart3, FileText, Download, Printer, CheckCircle } from "lucide-react";
import { StatusBadge } from "../components/StatusBadge";

interface ReportsViewProps {
  runs: QARun[];
}

export const ReportsView: React.FC<ReportsViewProps> = ({ runs }) => {
  const completedRuns = runs.filter((r) => r.status === "COMPLETED");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          <span>Executive QA Reports & Artifact Exports</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Export audit summaries, CSV defect inventories, machine-readable JSON schemas, and print-ready executive reports.
        </p>
      </div>

      {/* Reports Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold uppercase text-slate-500 tracking-wider">
              <tr>
                <th className="py-3 px-4">Run Date</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Browser</th>
                <th className="py-3 px-4">QA Score</th>
                <th className="py-3 px-4">Issues Found</th>
                <th className="py-3 px-4 text-right">Download & Print</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {completedRuns.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 px-4 whitespace-nowrap font-medium text-slate-900">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="font-semibold text-slate-700">{r.scan_type}</span>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap capitalize">{r.browser}</td>
                  <td className="py-3 px-4 whitespace-nowrap font-bold text-blue-600">
                    {r.qa_score}/100
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="font-bold text-red-600">{r.total_issues}</span> defects
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                    {/* Printable HTML */}
                    <a
                      href={`/api/reports/${r.id}/html`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-900 text-white rounded text-xs font-semibold hover:bg-slate-800 transition"
                    >
                      <Printer className="w-3 h-3" />
                      <span>Print / HTML</span>
                    </a>

                    {/* JSON */}
                    <a
                      href={`/api/reports/${r.id}/json`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 border border-slate-200 rounded text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                    >
                      <FileText className="w-3 h-3" />
                      <span>JSON</span>
                    </a>

                    {/* CSV */}
                    <a
                      href={`/api/reports/${r.id}/csv`}
                      download
                      className="inline-flex items-center gap-1 px-2 py-1 border border-slate-200 rounded text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                    >
                      <Download className="w-3 h-3" />
                      <span>CSV</span>
                    </a>
                  </td>
                </tr>
              ))}
              {completedRuns.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No completed QA runs to report yet.
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

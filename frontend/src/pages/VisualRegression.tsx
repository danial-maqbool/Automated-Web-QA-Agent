import React, { useState, useEffect } from "react";
import { Baseline, Project, PageRecord } from "../api/types";
import { api } from "../api/client";
import { Eye, Check, AlertTriangle, RefreshCw, Layers } from "lucide-react";

interface VisualRegressionProps {
  currentProject: Project | null;
  pages: PageRecord[];
}

export const VisualRegression: React.FC<VisualRegressionProps> = ({
  currentProject,
  pages,
}) => {
  const [baselines, setBaselines] = useState<Baseline[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    if (currentProject) {
      loadBaselines();
    }
  }, [currentProject]);

  const loadBaselines = async () => {
    if (!currentProject) return;
    setLoading(true);
    try {
      const data = await api.getBaselines(currentProject.id);
      setBaselines(data);
    } catch (err) {
      console.error("Failed to load baselines:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSetBaseline = async (pageUrl: string, screenshotPath: string) => {
    if (!currentProject) return;
    try {
      await api.createBaseline(currentProject.id, pageUrl, screenshotPath);
      await loadBaselines();
    } catch (err) {
      console.error("Failed to set baseline:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Eye className="w-5 h-5 text-blue-600" />
          <span>Visual Regression Testing</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Compare pixel-level UI drift against saved reference baselines with configurable anti-aliasing tolerance.
        </p>
      </div>

      {/* Baselines Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Active Baseline References ({baselines.length})
          </h3>
          <button
            onClick={loadBaselines}
            className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-slate-50 transition cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold uppercase text-slate-500">
              <tr>
                <th className="py-3 px-4">Page Target</th>
                <th className="py-3 px-4">Viewport</th>
                <th className="py-3 px-4">Browser</th>
                <th className="py-3 px-4">Created Date</th>
                <th className="py-3 px-4 text-right">Reference Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {baselines.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 px-4 font-mono font-medium text-slate-900 truncate max-w-xs">
                    {b.page_url}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">{b.viewport}</td>
                  <td className="py-3 px-4 whitespace-nowrap capitalize">{b.browser}</td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                    {new Date(b.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <a
                      href={`/artifacts/${b.screenshot_path}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 font-semibold hover:underline text-xs"
                    >
                      View Baseline PNG
                    </a>
                  </td>
                </tr>
              ))}
              {baselines.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400">
                    No visual baselines established yet. Set baselines from discovered pages below.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pages available to set as baseline */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
          Available Screenshots to Save as Baseline
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {pages
            .filter((p) => !!p.screenshot_path)
            .map((p) => (
              <div key={p.id} className="border border-slate-200 rounded-lg p-3 bg-slate-50/50">
                <div className="font-mono text-xs font-semibold text-slate-800 truncate mb-1">
                  {p.path || p.url}
                </div>
                <div className="border border-slate-200 rounded overflow-hidden bg-slate-900 mb-2">
                  <img
                    src={`/artifacts/${p.screenshot_path}`}
                    alt="Current Screenshot"
                    className="w-full h-32 object-cover object-top"
                  />
                </div>
                <button
                  onClick={() => handleSetBaseline(p.url, p.screenshot_path!)}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700 transition cursor-pointer"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Set as Baseline</span>
                </button>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

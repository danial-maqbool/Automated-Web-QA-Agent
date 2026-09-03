import React, { useState } from "react";
import { PageRecord } from "../api/types";
import { Search, Globe, Clock, ExternalLink, Image as ImageIcon } from "lucide-react";

interface PageExplorerProps {
  pages: PageRecord[];
}

export const PageExplorer: React.FC<PageExplorerProps> = ({ pages }) => {
  const [search, setSearch] = useState("");
  const [selectedScreenshot, setSelectedScreenshot] = useState<string | null>(null);

  const filtered = pages.filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return p.url.toLowerCase().includes(q) || (p.title || "").toLowerCase().includes(q);
  });

  return (
    <div className="space-y-4">
      {/* Search Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search pages by URL or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="text-xs font-semibold text-slate-500">
          Discovered Routes: <span className="text-slate-900 font-bold">{pages.length}</span>
        </div>
      </div>

      {/* Pages Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold uppercase text-slate-500 tracking-wider">
              <tr>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Route / Path</th>
                <th className="py-3 px-4">Page Title</th>
                <th className="py-3 px-4">Load Time</th>
                <th className="py-3 px-4">Last Inspected</th>
                <th className="py-3 px-4 text-right">Screenshot</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                        p.status_code === 200
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-red-50 text-red-700 border border-red-200"
                      }`}
                    >
                      {p.status_code || "N/A"}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono font-medium text-slate-900 max-w-sm truncate">
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:underline text-blue-600 flex items-center gap-1"
                    >
                      <span>{p.path || p.url}</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  </td>
                  <td className="py-3 px-4 text-slate-600 max-w-xs truncate">
                    {p.title || "<Untitled>"}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap font-mono text-slate-500">
                    {p.load_time_ms ? `${Math.round(p.load_time_ms)} ms` : "—"}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400">
                    {p.last_tested_at ? new Date(p.last_tested_at).toLocaleString() : "Never"}
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    {p.screenshot_path ? (
                      <button
                        onClick={() => setSelectedScreenshot(p.screenshot_path!)}
                        className="p-1 rounded text-blue-600 hover:bg-blue-50 transition cursor-pointer"
                        title="View page screenshot"
                      >
                        <ImageIcon className="w-4 h-4" />
                      </button>
                    ) : (
                      <span className="text-slate-300 text-[11px]">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No pages found matching filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Screenshot Lightbox */}
      {selectedScreenshot && (
        <div
          onClick={() => setSelectedScreenshot(null)}
          className="fixed inset-0 z-50 bg-slate-900/75 flex items-center justify-center p-6 backdrop-blur-xs cursor-pointer"
        >
          <div className="bg-white p-2 rounded-xl max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl">
            <img
              src={`/artifacts/${selectedScreenshot}`}
              alt="Page Screenshot"
              className="w-full h-auto max-h-[80vh] object-contain rounded-lg"
            />
            <p className="text-xs text-center text-slate-500 mt-2 font-mono">
              /artifacts/{selectedScreenshot} (Click anywhere to close)
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

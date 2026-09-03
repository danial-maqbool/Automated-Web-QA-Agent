import React from "react";
import { Project } from "../api/types";
import { Play, Sparkles, Zap, Shield, Plus } from "lucide-react";

interface TopBarProps {
  projects: Project[];
  selectedProject: Project | null;
  onSelectProject: (p: Project) => void;
  onNewProject: () => void;
  onStartScan: (type: "QUICK_SCAN" | "FULL_SCAN") => void;
  onOneClickDemo: () => void;
  isScanning: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  projects,
  selectedProject,
  onSelectProject,
  onNewProject,
  onStartScan,
  onOneClickDemo,
  isScanning,
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
      {/* Project Selector */}
      <div className="flex items-center gap-3">
        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Project:</label>
        <div className="relative">
          <select
            value={selectedProject?.id || ""}
            onChange={(e) => {
              const p = projects.find((x) => x.id === e.target.value);
              if (p) onSelectProject(p);
            }}
            className="bg-slate-50 border border-slate-200 text-slate-900 text-sm font-semibold rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.base_url})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onNewProject}
          title="Create New QA Project"
          className="p-1.5 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 hover:text-blue-600 transition"
        >
          <Plus className="w-4 h-4" />
        </button>

        {selectedProject && (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
            <Shield className="w-3 h-3 text-emerald-600" />
            Production Env
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {/* One Click Demo QA (Req 125) */}
        <button
          onClick={onOneClickDemo}
          disabled={isScanning}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-purple-200 bg-purple-50 text-purple-700 text-xs font-semibold rounded-lg hover:bg-purple-100 transition cursor-pointer disabled:opacity-50"
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-600" />
          <span>Run Demo QA</span>
        </button>

        {/* Quick Scan */}
        <button
          onClick={() => onStartScan("QUICK_SCAN")}
          disabled={isScanning || !selectedProject}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50 transition cursor-pointer disabled:opacity-50"
        >
          <Zap className="w-3.5 h-3.5 text-amber-500" />
          <span>Quick Scan</span>
        </button>

        {/* Full Scan */}
        <button
          onClick={() => onStartScan("FULL_SCAN")}
          disabled={isScanning || !selectedProject}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 shadow-xs transition cursor-pointer disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{isScanning ? "Scanning in Progress..." : "Run Full Scan"}</span>
        </button>
      </div>
    </header>
  );
};

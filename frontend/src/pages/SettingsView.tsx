import React from "react";
import { Project } from "../api/types";
import { Settings, Shield, Globe, Filter, Trash2 } from "lucide-react";

interface SettingsViewProps {
  currentProject: Project | null;
  onDeleteProject?: (id: string) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  currentProject,
  onDeleteProject,
}) => {
  if (!currentProject) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400">
        Select a project to configure settings.
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Settings className="w-5 h-5 text-blue-600" />
          <span>Project Settings: {currentProject.name}</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Manage target environments, crawl scope, ignore patterns, and safety restrictions.
        </p>
      </div>

      {/* General Config */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-slate-900">General Target Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">Project Name</label>
            <input
              type="text"
              readOnly
              value={currentProject.name}
              className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase">Base Target URL</label>
            <input
              type="text"
              readOnly
              value={currentProject.base_url}
              className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-700"
            />
          </div>
        </div>
      </div>

      {/* Safety Rules */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-600" />
          <span>Safe Form & Action Enforcement</span>
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Destructive buttons matching keywords (<code>delete</code>, <code>pay</code>, <code>purchase</code>, <code>checkout</code>, <code>cancel subscription</code>) are automatically blocked during exploratory crawling.
        </p>
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium">
          ✓ Active: Safe Form Values (Name: QA Test User, Email: qa.test@example.com, Phone: 03001234567)
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 space-y-2">
        <h3 className="text-sm font-bold text-red-900">Danger Zone</h3>
        <p className="text-xs text-red-700">
          Deleting this project removes all historical runs, detected issues, page records, and screenshot artifacts.
        </p>
        <div className="pt-2">
          <button
            onClick={() => {
              if (confirm(`Delete project "${currentProject.name}" and all historical test data?`)) {
                onDeleteProject?.(currentProject.id);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Project</span>
          </button>
        </div>
      </div>
    </div>
  );
};

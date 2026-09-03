import React from "react";
import { Issue } from "../api/types";
import { Accessibility, ShieldAlert, CheckCircle2, Code } from "lucide-react";
import { StatusBadge } from "../components/StatusBadge";

interface AccessibilityViewProps {
  issues: Issue[];
}

export const AccessibilityView: React.FC<AccessibilityViewProps> = ({ issues }) => {
  const a11yIssues = issues.filter((i) => i.category === "Accessibility");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Accessibility className="w-5 h-5 text-purple-600" />
            <span>WCAG 2.1 AA Accessibility Audit</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic accessibility verification powered by local axe-core. Scans ARIA roles, color contrast, keyboard navigable focus, form labels, and image alt text.
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-purple-600">{a11yIssues.length}</div>
          <div className="text-xs text-slate-500 font-medium">Detected Violations</div>
        </div>
      </div>

      {/* Violations List */}
      <div className="space-y-3">
        {a11yIssues.map((iss) => (
          <div key={iss.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <StatusBadge type="severity" value={iss.severity} />
                  <span className="text-xs font-mono bg-purple-50 text-purple-700 px-2 py-0.5 rounded border border-purple-200">
                    WCAG AA
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900">{iss.title}</h3>
                <p className="text-xs text-slate-500 mt-0.5 font-mono">{iss.page_url}</p>
              </div>
              <span className="text-xs font-bold text-slate-400">
                Confidence: {Math.round(iss.confidence * 100)}%
              </span>
            </div>

            <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100">
              {iss.description}
            </p>

            {iss.selector && (
              <div className="flex items-center gap-2">
                <Code className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <code className="text-xs text-slate-800 bg-slate-100 px-2 py-1 rounded font-mono truncate">
                  {iss.selector}
                </code>
              </div>
            )}
          </div>
        ))}

        {a11yIssues.length === 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
            <h4 className="text-sm font-bold text-slate-800">No Accessibility Violations Detected</h4>
            <p className="text-xs text-slate-500 mt-1">
              All inspected elements satisfy WCAG 2.1 AA accessibility standards.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

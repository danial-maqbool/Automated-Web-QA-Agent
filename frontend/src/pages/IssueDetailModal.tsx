import React, { useState } from "react";
import { Issue } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../api/client";
import {
  X,
  Copy,
  Check,
  ExternalLink,
  Shield,
  Clock,
  Layers,
  Terminal,
  Wifi,
  Image as ImageIcon
} from "lucide-react";

interface IssueDetailModalProps {
  issue: Issue;
  onClose: () => void;
  onUpdate: (updated: Issue) => void;
}

export const IssueDetailModal: React.FC<IssueDetailModalProps> = ({
  issue,
  onClose,
  onUpdate,
}) => {
  const [activeTab, setActiveTab] = useState<"overview" | "repro" | "screenshot" | "console" | "network">("overview");
  const [copied, setCopied] = useState(false);
  const [updating, setUpdating] = useState(false);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleStatusChange = async (newStatus: string) => {
    setUpdating(true);
    try {
      const updated = await api.updateIssue(issue.id, { status: newStatus });
      onUpdate(updated);
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdating(false);
    }
  };

  const handleCopyMarkdown = async () => {
    try {
      const md = await api.getIssueMarkdown(issue.id);
      await navigator.clipboard.writeText(md);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy markdown:", err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-xl max-w-3xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <StatusBadge type="severity" value={issue.severity} />
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {issue.category}
              </span>
              <StatusBadge type="status" value={issue.status} />
            </div>
            <h2 className="text-lg font-bold text-slate-900">{issue.title}</h2>
            <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
              <span>URL: <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200">{issue.page_url}</code></span>
              <span>•</span>
              <span>Occurrences: <strong>{issue.occurrence_count}</strong></span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center px-6 border-b border-slate-200 bg-white gap-4 text-xs font-semibold">
          {[
            { id: "overview", label: "Defect Overview", icon: <Layers className="w-4 h-4" /> },
            { id: "repro", label: "Reproduction Steps", icon: <Clock className="w-4 h-4" /> },
            { id: "screenshot", label: "Screenshot Evidence", icon: <ImageIcon className="w-4 h-4" /> },
            { id: "console", label: "Console Logs", icon: <Terminal className="w-4 h-4" /> },
            { id: "network", label: "Network Evidence", icon: <Wifi className="w-4 h-4" /> },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-1.5 py-3 border-b-2 cursor-pointer transition ${
                activeTab === t.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.icon}
              <span>{t.label}</span>
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4 text-sm">
          {activeTab === "overview" && (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Description</h4>
                <p className="mt-1 text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                  {issue.description}
                </p>
              </div>

              {issue.selector && (
                <div>
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Target Element Selector</h4>
                  <code className="mt-1 block bg-slate-900 text-slate-200 text-xs p-2.5 rounded-lg font-mono">
                    {issue.selector}
                  </code>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <h4 className="text-xs font-semibold uppercase text-slate-400">First Detected</h4>
                  <div className="text-xs font-medium text-slate-800 mt-1">
                    {new Date(issue.first_detected_at).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <h4 className="text-xs font-semibold uppercase text-slate-400">Detection Confidence</h4>
                  <div className="text-xs font-bold text-blue-600 mt-1">
                    {Math.round(issue.confidence * 100)}%
                  </div>
                </div>
              </div>

              {issue.affected_pages && issue.affected_pages.length > 1 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-1">
                    Affected Pages ({issue.affected_pages.length})
                  </h4>
                  <div className="max-h-32 overflow-y-auto space-y-1 bg-slate-50 p-2 rounded-lg border border-slate-100 text-xs">
                    {issue.affected_pages.map((p, idx) => (
                      <div key={idx} className="truncate text-slate-600 font-mono">
                        {p}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "repro" && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Step-by-step Reproduction</h4>
              {issue.reproduction_steps && issue.reproduction_steps.length > 0 ? (
                <ol className="list-decimal list-inside space-y-2 text-xs bg-slate-50 p-4 rounded-lg border border-slate-100">
                  {issue.reproduction_steps.map((s, idx) => (
                    <li key={idx} className="text-slate-800 font-medium">
                      <span className="font-semibold text-blue-600">{s.action.toUpperCase()}</span>{" "}
                      {s.target && <code>{s.target}</code>}{" "}
                      {s.value && <span className="text-slate-500">"{s.value}"</span>}
                    </li>
                  ))}
                </ol>
              ) : (
                <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg">
                  1. Navigate directly to <code className="text-blue-600">{issue.page_url}</code><br/>
                  2. Observe defect at selector <code>{issue.selector || "DOM context"}</code>
                </div>
              )}
            </div>
          )}

          {activeTab === "screenshot" && (
            <div>
              {issue.screenshot_path ? (
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-900 p-1">
                  <img
                    src={`/artifacts/${issue.screenshot_path}`}
                    alt="Defect Evidence Screenshot"
                    className="w-full h-auto max-h-96 object-contain rounded"
                  />
                  <div className="p-2 text-[11px] text-slate-400 text-center font-mono">
                    /artifacts/{issue.screenshot_path}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No visual screenshot artifact associated with this finding.
                </div>
              )}
            </div>
          )}

          {activeTab === "console" && (
            <div>
              {issue.console_evidence ? (
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-xs overflow-x-auto">
                  {JSON.stringify(issue.console_evidence, null, 2)}
                </pre>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No console error messages attached.
                </div>
              )}
            </div>
          )}

          {activeTab === "network" && (
            <div>
              {issue.network_evidence ? (
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-xs overflow-x-auto">
                  {JSON.stringify(issue.network_evidence, null, 2)}
                </pre>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs">
                  No network request failure records attached.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-white transition cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied for Jira/GitHub!" : "Copy as Markdown"}</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Status:</span>
            {["OPEN", "ACKNOWLEDGED", "FIXED", "IGNORED"].map((st) => (
              <button
                key={st}
                disabled={updating || issue.status === st}
                onClick={() => handleStatusChange(st)}
                className={`px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition ${
                  issue.status === st
                    ? "bg-slate-900 text-white"
                    : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-100"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

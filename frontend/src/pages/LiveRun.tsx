import React, { useState, useEffect } from "react";
import { QARun, RunEvent } from "../api/types";
import { api } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import {
  StopCircle,
  Globe,
  Activity,
  CheckCircle2,
  AlertCircle,
  Clock,
  Terminal,
  RefreshCw,
  ExternalLink
} from "lucide-react";

interface LiveRunProps {
  runId: string;
  onRunFinished: () => void;
}

export const LiveRun: React.FC<LiveRunProps> = ({ runId, onRunFinished }) => {
  const [run, setRun] = useState<QARun | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    let interval: any = null;

    const fetchStatus = async () => {
      try {
        const [rData, eData] = await Promise.all([
          api.getRun(runId),
          api.getRunEvents(runId),
        ]);
        setRun(rData);
        setEvents(eData);

        if (rData.status === "COMPLETED" || rData.status === "FAILED" || rData.status === "CANCELLED") {
          clearInterval(interval);
          onRunFinished();
        }
      } catch (err) {
        console.error("Error polling run status:", err);
      }
    };

    fetchStatus();
    interval = setInterval(fetchStatus, 1500);

    return () => clearInterval(interval);
  }, [runId]);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await api.cancelRun(runId);
    } catch (err) {
      console.error("Failed to cancel run:", err);
    } finally {
      setCancelling(false);
    }
  };

  if (!run) {
    return (
      <div className="flex items-center justify-center p-20 text-slate-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" />
        <span>Initializing telemetry...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 flex items-center justify-between shadow-xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge type="status" value={run.status} />
            <h2 className="text-lg font-bold text-slate-900">
              Active Quality Scan: {run.scan_type}
            </h2>
          </div>
          <p className="text-xs text-slate-500 flex items-center gap-2">
            <span>Run ID: <code>{run.id}</code></span>
            <span>•</span>
            <span>Browser: {run.browser} ({run.viewport_width}x{run.viewport_height})</span>
          </p>
        </div>

        {run.status === "RUNNING" && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="flex items-center gap-1.5 px-4 py-2 border border-red-200 bg-red-50 text-red-700 text-xs font-semibold rounded-lg hover:bg-red-100 transition cursor-pointer disabled:opacity-50"
          >
            <StopCircle className="w-4 h-4" />
            <span>{cancelling ? "Cancelling..." : "Stop Execution"}</span>
          </button>
        )}
      </div>

      {/* Real-time Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <span className="text-xs font-semibold text-slate-500 uppercase">Current Action</span>
          <div className="text-sm font-bold text-slate-900 mt-1 truncate">
            {run.current_action || "Processing DOM"}
          </div>
          <div className="text-xs text-blue-600 mt-1 truncate flex items-center gap-1">
            <Globe className="w-3 h-3 shrink-0" />
            <span className="truncate">{run.current_url || "Waiting..."}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <span className="text-xs font-semibold text-slate-500 uppercase">Pages Progress</span>
          <div className="text-xl font-bold text-slate-900 mt-1">
            {run.pages_tested} <span className="text-xs font-normal text-slate-400">/ {run.pages_discovered} discovered</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <span className="text-xs font-semibold text-slate-500 uppercase">Issues Discovered</span>
          <div className="text-xl font-bold text-red-600 mt-1">
            {run.total_issues}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            {run.critical_issues} Crit, {run.high_issues} High
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <span className="text-xs font-semibold text-slate-500 uppercase">Current Score</span>
          <div className="text-xl font-bold text-blue-600 mt-1">
            {run.qa_score} <span className="text-xs font-normal text-slate-400">/ 100</span>
          </div>
        </div>
      </div>

      {/* Real-time Event Feed */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs">
        <div className="px-4 py-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2 font-mono">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-200 font-semibold">Live Browser Execution Stream</span>
          </div>
          <span>{events.length} events logged</span>
        </div>
        <div className="p-4 font-mono text-xs text-slate-300 max-h-96 overflow-y-auto space-y-1.5">
          {events.map((e) => (
            <div key={e.id} className="flex items-start gap-2">
              <span className="text-slate-500 shrink-0">
                {new Date(e.timestamp).toLocaleTimeString()}
              </span>
              <span
                className={`font-bold shrink-0 ${
                  e.level === "SUCCESS"
                    ? "text-emerald-400"
                    : e.level === "ERROR"
                    ? "text-red-400"
                    : e.level === "WARNING"
                    ? "text-amber-400"
                    : "text-blue-400"
                }`}
              >
                [{e.level}]
              </span>
              <span className="break-all">{e.message}</span>
              {e.url && (
                <span className="text-slate-500 truncate max-w-xs">({e.url})</span>
              )}
            </div>
          ))}
          {events.length === 0 && (
            <p className="text-slate-500 italic">Waiting for initial Playwright events...</p>
          )}
        </div>
      </div>
    </div>
  );
};

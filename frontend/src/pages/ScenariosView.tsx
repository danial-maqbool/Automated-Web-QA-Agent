import React, { useState, useEffect } from "react";
import { TestScenario, Project } from "../api/types";
import { api } from "../api/client";
import { Workflow, Play, Plus, Code, CheckCircle, AlertCircle, Trash2 } from "lucide-react";

interface ScenariosViewProps {
  currentProject: Project | null;
}

export const ScenariosView: React.FC<ScenariosViewProps> = ({ currentProject }) => {
  const [scenarios, setScenarios] = useState<TestScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [execResult, setExecResult] = useState<any>(null);
  const [tsCode, setTsCode] = useState<string | null>(null);

  // New scenario form modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newScenarioName, setNewScenarioName] = useState("");
  const [steps, setSteps] = useState<Array<{ action_type: string; target: string; value: string; expected_value: string }>>([
    { action_type: "navigate", target: "http://localhost:8000/demo", value: "", expected_value: "" },
    { action_type: "assert_text", target: "", value: "", expected_value: "WebQA Reference Defect Fixture" },
  ]);

  useEffect(() => {
    if (currentProject) {
      loadScenarios();
    }
  }, [currentProject]);

  const loadScenarios = async () => {
    if (!currentProject) return;
    setLoading(true);
    try {
      const data = await api.getScenarios(currentProject.id);
      setScenarios(data);
    } catch (err) {
      console.error("Failed to load scenarios:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (id: string) => {
    setExecutingId(id);
    setExecResult(null);
    try {
      const result = await api.executeScenario(id);
      setExecResult(result);
    } catch (err: any) {
      setExecResult({ passed: false, error: err.message });
    } finally {
      setExecutingId(null);
    }
  };

  const handleExportPlaywright = async (id: string) => {
    try {
      const code = await api.exportPlaywrightCode(id);
      setTsCode(code);
    } catch (err) {
      console.error("Failed to export TS code:", err);
    }
  };

  const handleAddStep = () => {
    setSteps([...steps, { action_type: "click", target: "", value: "", expected_value: "" }]);
  };

  const handleSaveScenario = async () => {
    if (!currentProject || !newScenarioName.trim()) return;
    try {
      await api.createScenario(currentProject.id, {
        name: newScenarioName,
        steps: steps.map((s, idx) => ({ ...s, order_index: idx, is_optional: false })),
      });
      setShowCreateModal(false);
      setNewScenarioName("");
      await loadScenarios();
    } catch (err) {
      console.error("Failed to save scenario:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Workflow className="w-5 h-5 text-blue-600" />
            <span>Automated Test Scenarios & Assertion Engine</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Build repeatable multi-step workflows, verify custom DOM assertions, and export to Playwright TypeScript.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Scenario</span>
        </button>
      </div>

      {/* Execution Results Alert */}
      {execResult && (
        <div
          className={`p-4 rounded-xl border flex items-start justify-between ${
            execResult.passed
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          <div className="flex items-start gap-2">
            {execResult.passed ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-bold text-sm">
                {execResult.passed ? "All Scenario Steps Passed!" : "Scenario Execution Failed"}
              </div>
              <p className="text-xs mt-1">
                Executed {execResult.executed_steps_count} of {execResult.steps_count} steps.
              </p>
            </div>
          </div>
          <button
            onClick={() => setExecResult(null)}
            className="text-xs font-semibold underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Scenarios List */}
      <div className="space-y-4">
        {scenarios.map((sc) => (
          <div key={sc.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">{sc.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {sc.steps?.length || 0} automated steps configured
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleExportPlaywright(sc.id)}
                  className="flex items-center gap-1 px-2.5 py-1.5 border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50 cursor-pointer"
                >
                  <Code className="w-3.5 h-3.5" />
                  <span>Export Playwright TS</span>
                </button>
                <button
                  onClick={() => handleExecute(sc.id)}
                  disabled={executingId === sc.id}
                  className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{executingId === sc.id ? "Running..." : "Run Scenario"}</span>
                </button>
              </div>
            </div>

            {/* Steps Preview */}
            <div className="space-y-1.5 pt-2 border-t border-slate-100">
              {sc.steps?.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs font-mono bg-slate-50 p-2 rounded border border-slate-100"
                >
                  <span className="text-slate-400 font-bold">{idx + 1}.</span>
                  <span className="font-semibold text-blue-600 uppercase">{step.action_type}</span>
                  {step.target && <span className="text-slate-800">{step.target}</span>}
                  {step.value && <span className="text-slate-500">value="{step.value}"</span>}
                  {step.expected_value && (
                    <span className="text-emerald-700 font-semibold">expected="{step.expected_value}"</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}

        {scenarios.length === 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400">
            <Workflow className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <h4 className="text-sm font-bold text-slate-800">No Test Scenarios Yet</h4>
            <p className="text-xs text-slate-500 mt-1">
              Create a custom workflow or click "Launch Benchmark Demo" to test pre-configured flows.
            </p>
          </div>
        )}
      </div>

      {/* Playwright Code Modal */}
      {tsCode && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-6 backdrop-blur-xs">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between text-white">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Code className="w-4 h-4 text-emerald-400" />
                <span>Generated Playwright TypeScript Test</span>
              </h3>
              <button
                onClick={() => setTsCode(null)}
                className="text-slate-400 hover:text-white cursor-pointer text-xs"
              >
                Close
              </button>
            </div>
            <pre className="bg-slate-950 p-4 rounded-lg text-emerald-400 font-mono text-xs overflow-x-auto max-h-96">
              {tsCode}
            </pre>
            <div className="flex justify-end">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(tsCode);
                  setTsCode(null);
                }}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700 cursor-pointer"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Scenario Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-6 backdrop-blur-xs">
          <div className="bg-white border border-slate-200 rounded-xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-slate-900">Create Test Scenario</h3>
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase">Scenario Name</label>
              <input
                type="text"
                value={newScenarioName}
                onChange={(e) => setNewScenarioName(e.target.value)}
                placeholder="e.g. Critical User Signup Flow"
                className="w-full mt-1 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900"
              />
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              <label className="text-xs font-semibold text-slate-500 uppercase">Steps</label>
              {steps.map((st, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-slate-50 p-2 rounded border border-slate-200 text-xs">
                  <select
                    value={st.action_type}
                    onChange={(e) => {
                      const updated = [...steps];
                      updated[idx].action_type = e.target.value;
                      setSteps(updated);
                    }}
                    className="bg-white border border-slate-200 rounded px-2 py-1 font-semibold"
                  >
                    <option value="navigate">navigate</option>
                    <option value="click">click</option>
                    <option value="fill">fill</option>
                    <option value="wait">wait</option>
                    <option value="assert_text">assert_text</option>
                    <option value="assert_visibility">assert_visibility</option>
                  </select>
                  <input
                    type="text"
                    placeholder="Target selector or URL"
                    value={st.target}
                    onChange={(e) => {
                      const updated = [...steps];
                      updated[idx].target = e.target.value;
                      setSteps(updated);
                    }}
                    className="flex-1 bg-white border border-slate-200 rounded px-2 py-1"
                  />
                  <input
                    type="text"
                    placeholder="Value / Expected"
                    value={st.expected_value || st.value}
                    onChange={(e) => {
                      const updated = [...steps];
                      updated[idx].expected_value = e.target.value;
                      updated[idx].value = e.target.value;
                      setSteps(updated);
                    }}
                    className="w-32 bg-white border border-slate-200 rounded px-2 py-1"
                  />
                  <button
                    onClick={() => setSteps(steps.filter((_, i) => i !== idx))}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <button
                onClick={handleAddStep}
                className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
              >
                <Plus className="w-3 h-3" /> Add Step
              </button>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-3 py-1.5 border border-slate-200 rounded text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveScenario}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700 cursor-pointer"
              >
                Save Scenario
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

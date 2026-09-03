import { Project, QARun, Issue, PageRecord, Baseline, TestScenario, RunEvent } from "./types";

const API_BASE = "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status}: ${errorText || res.statusText}`);
  }

  if (res.status === 204) {
    return null as unknown as T;
  }

  return res.json();
}

export const api = {
  // Projects
  getProjects: () => request<Project[]>("/api/projects"),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  createProject: (data: { name: string; base_url: string; description?: string }) =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify(data) }),
  deleteProject: (id: string) => request<void>(`/api/projects/${id}`, { method: "DELETE" }),

  // Runs
  getRuns: (projectId?: string) =>
    request<QARun[]>(`/api/runs${projectId ? `?project_id=${projectId}` : ""}`),
  getRun: (id: string) => request<QARun>(`/api/runs/${id}`),
  createRun: (data: { project_id: string; scan_type: string; browser?: string }) =>
    request<QARun>("/api/runs", { method: "POST", body: JSON.stringify(data) }),
  cancelRun: (id: string) => request<{ status: string }>(`/api/runs/${id}/cancel`, { method: "POST" }),
  getRunEvents: (id: string) => request<RunEvent[]>(`/api/runs/${id}/events`),

  // Issues
  getIssues: (params: { projectId?: string; severity?: string; category?: string; status?: string; search?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.projectId) q.append("project_id", params.projectId);
    if (params.severity) q.append("severity", params.severity);
    if (params.category) q.append("category", params.category);
    if (params.status) q.append("status", params.status);
    if (params.search) q.append("search", params.search);
    return request<Issue[]>(`/api/issues?${q.toString()}`);
  },
  getIssue: (id: string) => request<Issue>(`/api/issues/${id}`),
  updateIssue: (id: string, data: { status?: string; severity?: string; notes?: string }) =>
    request<Issue>(`/api/issues/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  getIssueMarkdown: (id: string) =>
    fetch(`/api/issues/${id}/export-markdown`).then(r => r.text()),

  // Pages
  getPages: (projectId?: string) =>
    request<PageRecord[]>(`/api/pages${projectId ? `?project_id=${projectId}` : ""}`),
  getPage: (id: string) => request<PageRecord>(`/api/pages/${id}`),
  getPageVisits: (pageId: string) => request<any[]>(`/api/pages/${pageId}/visits`),

  // Baselines
  getBaselines: (projectId?: string) =>
    request<Baseline[]>(`/api/baselines${projectId ? `?project_id=${projectId}` : ""}`),
  createBaseline: (projectId: string, pageUrl: string, screenshotPath: string) =>
    request<Baseline>(`/api/baselines?project_id=${projectId}&page_url=${encodeURIComponent(pageUrl)}&screenshot_path=${encodeURIComponent(screenshotPath)}`, { method: "POST" }),
  compareVisual: (baselineId: string, currentScreenshot: string, runId: string) =>
    request<any>(`/api/baselines/compare?baseline_id=${baselineId}&current_screenshot_path=${encodeURIComponent(currentScreenshot)}&run_id=${runId}`, { method: "POST" }),

  // Scenarios
  getScenarios: (projectId?: string) =>
    request<TestScenario[]>(`/api/scenarios${projectId ? `?project_id=${projectId}` : ""}`),
  createScenario: (projectId: string, data: any) =>
    request<TestScenario>(`/api/scenarios?project_id=${projectId}`, { method: "POST", body: JSON.stringify(data) }),
  executeScenario: (id: string) => request<any>(`/api/scenarios/${id}/execute`, { method: "POST" }),
  exportPlaywrightCode: (id: string) =>
    fetch(`/api/scenarios/${id}/export-playwright`).then(r => r.text()),

  // Reports
  getReportJson: (runId: string) => request<any>(`/api/reports/${runId}/json`),

  // Demo
  oneClickDemo: () => request<any>("/api/demo/one-click-demo", { method: "POST" }),
};

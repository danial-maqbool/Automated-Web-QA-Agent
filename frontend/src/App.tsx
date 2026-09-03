import React, { useState, useEffect } from "react";
import { Project, QARun, Issue, PageRecord } from "./api/types";
import { api } from "./api/client";
import { Sidebar, NavTab } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { Dashboard } from "./pages/Dashboard";
import { LiveRun } from "./pages/LiveRun";
import { IssueExplorer } from "./pages/IssueExplorer";
import { PageExplorer } from "./pages/PageExplorer";
import { VisualRegression } from "./pages/VisualRegression";
import { AccessibilityView } from "./pages/AccessibilityView";
import { ScenariosView } from "./pages/ScenariosView";
import { ReportsView } from "./pages/ReportsView";
import { RunsView } from "./pages/RunsView";
import { SettingsView } from "./pages/SettingsView";
import { FirstRunExperience } from "./pages/FirstRunExperience";
import { RefreshCw } from "lucide-react";

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [currentTab, setCurrentTab] = useState<NavTab>("dashboard");
  const [runs, setRuns] = useState<QARun[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [pages, setPages] = useState<PageRecord[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFirstRunModal, setShowFirstRunModal] = useState(false);

  // Load initial projects
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
      if (data.length > 0) {
        setSelectedProject((prev) => prev || data[0]);
      } else {
        setShowFirstRunModal(true);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setLoading(false);
    }
  };

  // Reload project data when selected project changes
  useEffect(() => {
    if (selectedProject) {
      loadProjectData(selectedProject.id);
    }
  }, [selectedProject]);

  const loadProjectData = async (projectId: string) => {
    try {
      const [rData, iData, pData] = await Promise.all([
        api.getRuns(projectId),
        api.getIssues({ projectId }),
        api.getPages(projectId),
      ]);
      setRuns(rData);
      setIssues(iData);
      setPages(pData);

      // Check if any run is currently running
      const active = rData.find((r) => r.status === "RUNNING" || r.status === "PENDING");
      if (active) {
        setActiveRunId(active.id);
      }
    } catch (err) {
      console.error("Failed to load project details:", err);
    }
  };

  const handleStartScan = async (scanType: "QUICK_SCAN" | "FULL_SCAN") => {
    if (!selectedProject) return;
    try {
      const run = await api.createRun({
        project_id: selectedProject.id,
        scan_type: scanType,
      });
      setActiveRunId(run.id);
      await loadProjectData(selectedProject.id);
    } catch (err) {
      console.error("Failed to start scan:", err);
    }
  };

  const handleOneClickDemo = async () => {
    setShowFirstRunModal(false);
    try {
      const res = await api.oneClickDemo();
      await loadProjects();
      const proj = await api.getProject(res.project_id);
      setSelectedProject(proj);
      setActiveRunId(res.run_id);
    } catch (err) {
      console.error("Failed to trigger demo:", err);
    }
  };

  const handleCreateProject = async (
    name: string,
    url: string,
    scanType: "QUICK_SCAN" | "FULL_SCAN"
  ) => {
    setShowFirstRunModal(false);
    try {
      const p = await api.createProject({ name, base_url: url });
      setProjects((prev) => [p, ...prev]);
      setSelectedProject(p);
      const run = await api.createRun({ project_id: p.id, scan_type: scanType });
      setActiveRunId(run.id);
    } catch (err) {
      console.error("Failed to create project:", err);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await api.deleteProject(projectId);
      const remaining = projects.filter((p) => p.id !== projectId);
      setProjects(remaining);
      setSelectedProject(remaining.length > 0 ? remaining[0] : null);
      if (remaining.length === 0) {
        setShowFirstRunModal(true);
      }
    } catch (err) {
      console.error("Failed to delete project:", err);
    }
  };

  const latestRun = runs.length > 0 ? runs[0] : null;

  return (
    <div className="flex h-screen overflow-hidden bg-[#F6F8FB]">
      {/* Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          // If viewing specific tab, keep active run in background
        }}
        openIssuesCount={issues.filter((i) => i.status === "OPEN").length}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* TopBar */}
        <TopBar
          projects={projects}
          selectedProject={selectedProject}
          onSelectProject={(p) => setSelectedProject(p)}
          onNewProject={() => setShowFirstRunModal(true)}
          onStartScan={handleStartScan}
          onOneClickDemo={handleOneClickDemo}
          isScanning={!!activeRunId}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64 text-slate-400">
              <RefreshCw className="w-5 h-5 animate-spin mr-2" />
              <span>Loading workspace...</span>
            </div>
          ) : (
            <>
              {/* Show Live Run view if scan is in progress and on dashboard or runs tab */}
              {activeRunId && (currentTab === "dashboard" || currentTab === "runs") ? (
                <LiveRun
                  runId={activeRunId}
                  onRunFinished={() => {
                    setActiveRunId(null);
                    if (selectedProject) loadProjectData(selectedProject.id);
                  }}
                />
              ) : (
                <>
                  {currentTab === "dashboard" && (
                    <Dashboard
                      currentProject={selectedProject}
                      latestRun={latestRun}
                      recentRuns={runs}
                      issues={issues}
                      pages={pages}
                      onNavigateToIssues={() => setCurrentTab("issues")}
                      onNavigateToRuns={() => setCurrentTab("runs")}
                      onNavigateToPages={() => setCurrentTab("pages")}
                      onRunDemo={handleOneClickDemo}
                    />
                  )}

                  {currentTab === "runs" && (
                    <RunsView
                      runs={runs}
                      onSelectRun={(runId) => setActiveRunId(runId)}
                    />
                  )}

                  {currentTab === "issues" && (
                    <IssueExplorer
                      issues={issues}
                      onIssueUpdated={(updated) => {
                        setIssues((prev) =>
                          prev.map((i) => (i.id === updated.id ? updated : i))
                        );
                      }}
                    />
                  )}

                  {currentTab === "pages" && <PageExplorer pages={pages} />}

                  {currentTab === "scenarios" && (
                    <ScenariosView currentProject={selectedProject} />
                  )}

                  {currentTab === "visual" && (
                    <VisualRegression
                      currentProject={selectedProject}
                      pages={pages}
                    />
                  )}

                  {currentTab === "accessibility" && (
                    <AccessibilityView issues={issues} />
                  )}

                  {currentTab === "reports" && <ReportsView runs={runs} />}

                  {currentTab === "settings" && (
                    <SettingsView
                      currentProject={selectedProject}
                      onDeleteProject={handleDeleteProject}
                    />
                  )}
                </>
              )}
            </>
          )}
        </main>
      </div>

      {/* First Run / New Project Modal */}
      {showFirstRunModal && (
        <FirstRunExperience
          onClose={projects.length > 0 ? () => setShowFirstRunModal(false) : undefined}
          onSubmit={handleCreateProject}
          onOneClickDemo={handleOneClickDemo}
        />
      )}
    </div>
  );
}

export default App;

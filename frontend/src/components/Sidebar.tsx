import React from "react";
import {
  LayoutDashboard,
  PlayCircle,
  AlertTriangle,
  FileText,
  Workflow,
  Eye,
  Accessibility,
  BarChart3,
  Settings,
  ShieldCheck,
  Globe
} from "lucide-react";

export type NavTab =
  | "dashboard"
  | "runs"
  | "issues"
  | "pages"
  | "scenarios"
  | "visual"
  | "accessibility"
  | "reports"
  | "settings";

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  openIssuesCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  openIssuesCount = 0,
}) => {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: "runs", label: "QA Runs", icon: <PlayCircle className="w-4 h-4" /> },
    {
      id: "issues",
      label: "Issues Explorer",
      icon: <AlertTriangle className="w-4 h-4" />,
      badge: openIssuesCount > 0 ? openIssuesCount : null,
    },
    { id: "pages", label: "Discovered Pages", icon: <FileText className="w-4 h-4" /> },
    { id: "scenarios", label: "Test Scenarios", icon: <Workflow className="w-4 h-4" /> },
    { id: "visual", label: "Visual Regression", icon: <Eye className="w-4 h-4" /> },
    { id: "accessibility", label: "Accessibility", icon: <Accessibility className="w-4 h-4" /> },
    { id: "reports", label: "Reports & Export", icon: <BarChart3 className="w-4 h-4" /> },
    { id: "settings", label: "Project Settings", icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-xs">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-bold text-slate-900 text-base leading-none">WebQA Agent</h1>
          <span className="text-[10px] text-blue-600 font-semibold uppercase tracking-wider">Enterprise QA</span>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id as NavTab)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition cursor-pointer ${
                isActive
                  ? "bg-blue-50/80 text-blue-700 font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? "text-blue-600" : "text-slate-400"}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge !== null && item.badge !== undefined && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    isActive ? "bg-blue-600 text-white" : "bg-red-100 text-red-700"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-100 text-xs text-slate-400 space-y-1">
        <div className="flex items-center gap-1.5 font-medium text-slate-600">
          <Globe className="w-3.5 h-3.5 text-slate-400" />
          <span>Local Engine Active</span>
        </div>
        <div className="text-[11px] text-slate-400">Deterministic QA Core • 100% Offline</div>
      </div>
    </aside>
  );
};

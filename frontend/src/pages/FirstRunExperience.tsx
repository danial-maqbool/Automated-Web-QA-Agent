import React, { useState } from "react";
import { ShieldCheck, Globe, Zap, Play, Sparkles, X } from "lucide-react";

interface FirstRunExperienceProps {
  onClose?: () => void;
  onSubmit: (name: string, url: string, scanType: "QUICK_SCAN" | "FULL_SCAN") => void;
  onOneClickDemo: () => void;
}

export const FirstRunExperience: React.FC<FirstRunExperienceProps> = ({
  onClose,
  onSubmit,
  onOneClickDemo,
}) => {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [scanType, setScanType] = useState<"QUICK_SCAN" | "FULL_SCAN">("QUICK_SCAN");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    const finalName = name.trim() || new URL(url.startsWith("http") ? url : `http://${url}`).hostname;
    const finalUrl = url.startsWith("http") ? url : `http://${url}`;
    onSubmit(finalName, finalUrl, scanType);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="bg-slate-900 p-6 text-white relative">
          {onClose && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-slate-400 hover:text-white cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          )}
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center mb-3 shadow-md">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-bold">Inspect a Website</h2>
          <p className="text-xs text-slate-300 mt-1">
            Automate link checking, console diagnostics, responsive layout inspection, and WCAG accessibility.
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          <div>
            <label className="font-bold text-slate-700 uppercase tracking-wider block mb-1">
              Target Website URL <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Globe className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                placeholder="https://example.com or http://localhost:3000"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="font-bold text-slate-700 uppercase tracking-wider block mb-1">
              Project Name (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. My Next.js SaaS Staging"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="font-bold text-slate-700 uppercase tracking-wider block mb-1">
              Scan Depth
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setScanType("QUICK_SCAN")}
                className={`p-3 rounded-lg border text-left cursor-pointer transition ${
                  scanType === "QUICK_SCAN"
                    ? "border-blue-600 bg-blue-50/50 text-blue-900"
                    : "border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100"
                }`}
              >
                <div className="font-bold flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span>Quick Scan</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Crawl up to 5 key pages</div>
              </button>

              <button
                type="button"
                onClick={() => setScanType("FULL_SCAN")}
                className={`p-3 rounded-lg border text-left cursor-pointer transition ${
                  scanType === "FULL_SCAN"
                    ? "border-blue-600 bg-blue-50/50 text-blue-900"
                    : "border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100"
                }`}
              >
                <div className="font-bold flex items-center gap-1">
                  <Play className="w-3.5 h-3.5 text-blue-600 fill-current" />
                  <span>Full Scan</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Deep crawl up to 25 pages</div>
              </button>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-bold text-sm hover:bg-blue-700 shadow-sm transition cursor-pointer"
            >
              Start Automated QA Audit
            </button>
          </div>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-slate-200"></div>
            <span className="flex-shrink mx-4 text-slate-400 text-[11px] uppercase">Or Test Offline</span>
            <div className="flex-grow border-t border-slate-200"></div>
          </div>

          <button
            type="button"
            onClick={onOneClickDemo}
            className="w-full py-2 bg-purple-50 border border-purple-200 text-purple-700 rounded-lg font-semibold text-xs hover:bg-purple-100 transition flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>Launch Pre-configured Benchmark Demo Website</span>
          </button>
        </form>
      </div>
    </div>
  );
};

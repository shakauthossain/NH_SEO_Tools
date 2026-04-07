import React from "react";

import { API_BASE_URL as API_URL } from "../api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Zap,
  Download,
  Globe,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  History,
  ExternalLink,
  Link as LinkIcon,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { CircularProgress } from "../components/CircularProgress";
import type { HistoryItem } from "../components/HistoryPanel";

export type AnalysisType = "seo" | "speed" | "both";
export type Status = "idle" | "analyzing" | "complete";

const PROGRESS_STEPS = [
  "Connecting to server",
  "Fetching performance metrics",
  "Analyzing core web vitals",
  "Evaluating content structure",
  "Compiling report",
];

interface AnalyzePageProps {
  url: string;
  setUrl: (v: string) => void;
  analysisType: AnalysisType;
  setAnalysisType: (v: AnalysisType) => void;
  status: Status;
  activeStep: number;
  auditData: any;
  viewingDetails: "seo" | "speed" | null;
  setViewingDetails: (v: "seo" | "speed" | null) => void;
  isLoggedIn: boolean;
  history: HistoryItem[];
  onAnalyze: (e: React.FormEvent) => Promise<void>;
  onReset: () => void;
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 300, damping: 24 },
  },
};

export default function AnalyzePage({
  url,
  setUrl,
  analysisType,
  setAnalysisType,
  status,
  activeStep,
  auditData,
  viewingDetails,
  setViewingDetails,
  isLoggedIn,
  history,
  onAnalyze,
  onReset,
}: AnalyzePageProps) {
  const navigate = useNavigate();

  return (
    <AnimatePresence mode="wait">
      {/* ── IDLE ─────────────────────────────────────────────────────────── */}
      {status === "idle" && (
        <motion.div
          key="idle"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="w-full flex flex-col"
        >
          <div className="mb-10">
            <h2 className="text-4xl font-semibold tracking-tight mb-4 text-text-main">
              Search Engine Intelligence
            </h2>
            <p className="text-text-muted text-lg max-w-xl">
              Enter a URL to analyze Technical SEO, Page Speed, and Core Web
              Vitals using the premium RankMath engine.
            </p>
          </div>

          <form onSubmit={onAnalyze} className="w-full max-w-2xl space-y-6">
            <div className="relative flex items-center bg-bg-main border border-border-subtle p-1.5 rounded-xl focus-within:border-border-focus focus-within:ring-1 focus-within:ring-border-focus">
              <div className="pl-3 pr-2">
                <Globe className="w-5 h-5 text-text-muted" />
              </div>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="example.com"
                className="flex-1 bg-transparent border-none outline-none text-base text-text-main py-2.5 px-2"
                required
              />
              <button
                type="submit"
                className="bg-accent text-accent-fg px-5 py-2.5 rounded-lg font-medium hover:bg-black/80 transition-colors flex items-center gap-2"
              >
                Analyze <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            <div className="flex">
              <div className="inline-flex bg-bg-card border border-border-subtle p-1 rounded-lg">
                {(["seo", "both", "speed"] as AnalysisType[]).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setAnalysisType(type)}
                    className={`relative px-6 py-2 text-sm font-medium transition-colors flex items-center gap-2 z-10 rounded-md ${
                      analysisType === type
                        ? "text-accent-fg"
                        : "text-text-muted hover:text-text-main"
                    }`}
                  >
                    {analysisType === type && (
                      <motion.div
                        layoutId="activeTab"
                        className="absolute inset-0 bg-accent rounded-md"
                      />
                    )}
                    <span className="relative z-10 flex items-center gap-2 capitalize">
                      {type === "both" ? "Full Audit" : type}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </form>

          {/* Recent Audits */}
          {isLoggedIn && history.length > 0 && (
            <div className="mt-16 w-full max-w-4xl">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2 text-text-main">
                <History className="w-5 h-5 text-text-muted" /> Recent Audits
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {history.slice(0, 6).map((item) => (
                  <div
                    key={`inline-${item.id}`}
                    className="p-5 rounded-xl bg-bg-card border border-border-subtle hover:border-border-focus cursor-pointer transition-colors"
                    onClick={() => {
                      const domain = item.url
                        .replace(/^(?:https?:\/\/)?(?:www\.)?/i, "")
                        .split("/")[0];
                      navigate(`/analyze/${domain}/${item.id}`);
                    }}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <span className="font-medium text-base truncate max-w-[200px] text-text-main">
                        {item.url}
                      </span>
                      <span className="text-sm text-text-muted">
                        {item.date}
                      </span>
                    </div>
                    <div className="flex gap-4">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs uppercase font-bold text-text-muted">
                          SEO
                        </span>
                        <span className="text-sm font-bold text-pass">
                          {item.seoGrade}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs uppercase font-bold text-text-muted">
                          SPEED
                        </span>
                        <span className="text-sm font-bold text-warn">
                          {item.speedGrade}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* ── ANALYZING ────────────────────────────────────────────────────── */}
      {status === "analyzing" && (
        <motion.div
          key="analyzing"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="w-full max-w-xl py-12"
        >
          <div className="flex items-center gap-4 mb-8">
            <Loader2 className="w-6 h-6 text-text-muted animate-spin" />
            <h2 className="text-2xl font-semibold tracking-tight text-text-main">
              Running Expert Scan...
            </h2>
          </div>
          <div className="w-full space-y-4">
            {PROGRESS_STEPS.map((step, index) => (
              <div
                key={step}
                className={`flex items-center gap-4 p-3 rounded-lg ${
                  index <= activeStep ? "opacity-100" : "opacity-30"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                    index < activeStep
                      ? "bg-pass text-bg-main"
                      : "border-2 border-accent"
                  }`}
                >
                  {index < activeStep ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span className="text-base text-text-main">{step}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── COMPLETE — summary cards ─────────────────────────────────────── */}
      {status === "complete" && !viewingDetails && (
        <motion.div
          key="complete"
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="w-full"
        >
          <div className="flex items-center justify-between mb-8 pb-6 border-b border-border-subtle">
            <div>
              <h2 className="text-3xl font-semibold text-text-main mb-2">
                Audit Results
              </h2>
              <p className="text-text-muted flex items-center gap-2 text-sm">
                <Globe className="w-4 h-4" /> {url}
              </p>
            </div>
            <button
              onClick={onReset}
              className="px-4 py-2 border border-border-subtle hover:border-border-focus rounded-lg text-sm font-medium transition-colors"
            >
              Reset
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* SEO card */}
            {auditData?.seo && (
              <motion.div
                variants={itemVariants}
                className="bg-bg-card border border-border-subtle rounded-xl p-6 hover:border-border-focus flex flex-col"
              >
                <div className="flex justify-between items-start mb-8">
                  <div className="flex items-center gap-3">
                    <Search className="w-5 h-5 text-accent" />
                    <h3 className="text-lg font-semibold">SEO Engine</h3>
                  </div>
                  <div className="text-4xl font-bold text-pass">
                    {auditData.seo.seo_score || "N/A"}
                  </div>
                </div>
                <div className="space-y-4 mb-8 flex-1">
                  <div className="relative h-1.5 w-full rounded-full overflow-hidden bg-bg-hover">
                    {/* SEO Health Bar - Direct Score Representation */}
                    <div 
                      className="absolute inset-y-0 left-0 bg-pass transition-all duration-500" 
                      style={{ 
                        width: `${auditData.seo.seo_score || 0}%`,
                      }} 
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2 pb-2 border-b border-border-subtle">
                    <div className="text-[10px] font-bold text-text-muted uppercase">Priority Fixes</div>
                    <div className="text-[10px] font-bold text-text-muted uppercase text-right">Status</div>
                  </div>

                  {(auditData.seo.seo_tests || [])
                    .filter((t: any) => t.status === "fail")
                    .slice(0, 3)
                    .map((test: any) => (
                      <div
                        key={test.title}
                        className="flex justify-between items-start py-1"
                      >
                        <div className="flex flex-col gap-0.5 max-w-[80%]">
                           <span className="text-text-main text-xs font-semibold capitalize whitespace-nowrap overflow-hidden text-ellipsis">
                             {test.title.split('?')[0].trim()}
                           </span>
                           <span className="text-text-muted text-[11px] line-clamp-1">
                             Critical SEO optimization required.
                           </span>
                        </div>
                        <span className="text-xs font-extrabold text-fail shrink-0">CRITICAL</span>
                      </div>
                    ))}
                  
                  {auditData.seo.seo_tests?.filter((t: any) => t.status === "fail").length === 0 && (
                    <div className="flex items-center gap-2 text-pass py-2">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-xs font-semibold">No critical issues found!</span>
                    </div>
                  )}
                </div>
                <div className="flex gap-3">
                  <a
                    href={`${API_URL}/reports/${auditData.id}_seo.html`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 bg-bg-hover border border-border-subtle py-2 rounded-lg text-sm font-medium text-center hover:bg-bg-card transition-colors flex items-center justify-center gap-2"
                  >
                    Deep Dive <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                  <a
                    href={`${API_URL}/reports/${auditData.id}_seo.pdf`}
                    className="p-2 border border-border-subtle rounded-lg text-text-muted hover:text-accent hover:border-accent transition-colors"
                    title="Download PDF"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </motion.div>
            )}

            {/* Speed card */}
            {auditData?.speed && (
              <motion.div
                variants={itemVariants}
                className="bg-bg-card border border-border-subtle rounded-xl p-6 hover:border-border-focus flex flex-col"
              >
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-3">
                    <Zap className="w-5 h-5 text-warn" />
                    <h3 className="text-lg font-semibold">Page Experience</h3>
                  </div>
                  <div className="flex gap-4">
                    <div className="text-center">
                      <div className="text-[10px] uppercase font-bold text-text-muted mb-0.5">Mobile</div>
                      <div className="text-3xl font-bold text-pass leading-tight">
                        {auditData.speed.mobile?.perf_score || auditData.speed.perf_score || "N/A"}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] uppercase font-bold text-text-muted mb-0.5">Desktop</div>
                      <div className="text-3xl font-bold text-accent leading-tight">
                        {auditData.speed.desktop?.perf_score || "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="space-y-4 mb-8 flex-1">
                  <div className="relative h-1.5 w-full rounded-full bg-bg-hover overflow-hidden">
                    {/* Page Experience Bar - Mobile Only */}
                    <div 
                      className="absolute inset-y-0 left-0 bg-pass transition-all duration-500" 
                      style={{ width: `${(auditData.speed.mobile?.perf_score || auditData.speed.perf_score || 0)}%` }} 
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2 pb-2 border-b border-border-subtle">
                    <div className="text-[10px] font-bold text-text-muted uppercase">Core Vitals (Mobile)</div>
                    <div className="text-[10px] font-bold text-text-muted uppercase text-right">Value</div>
                  </div>

                  <div className="flex justify-between items-start py-1">
                    <div className="flex flex-col gap-0.5">
                       <span className="text-text-main text-xs font-semibold uppercase">FCP</span>
                       <span className="text-text-muted text-[11px]">First Contentful Paint</span>
                    </div>
                    <span className="text-xs font-extrabold text-text-main shrink-0">
                      {auditData.speed.mobile?.fcp || auditData.speed.metrics?.fcp}
                    </span>
                  </div>

                  <div className="flex justify-between items-start py-1">
                    <div className="flex flex-col gap-0.5">
                       <span className="text-text-main text-xs font-semibold uppercase">LCP</span>
                       <span className="text-text-muted text-[11px]">Largest Contentful Paint</span>
                    </div>
                    <span className="text-xs font-extrabold text-text-main shrink-0">
                      {auditData.speed.mobile?.lcp || auditData.speed.metrics?.lcp}
                    </span>
                  </div>

                  <div className="flex justify-between items-start py-1">
                    <div className="flex flex-col gap-0.5">
                       <span className="text-text-main text-xs font-semibold uppercase">CLS</span>
                       <span className="text-text-muted text-[11px]">Cumulative Layout Shift</span>
                    </div>
                    <span className="text-xs font-extrabold text-text-main shrink-0">
                      {auditData.speed.mobile?.cls || auditData.speed.metrics?.cls}
                    </span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <a
                    href={`${API_URL}/reports/${auditData.id}_speed.html`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 bg-bg-hover border border-border-subtle py-2 rounded-lg text-sm font-medium text-center hover:bg-bg-card transition-colors flex items-center justify-center gap-2"
                  >
                    Metric Breakdown <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                  <a
                    href={`${API_URL}/reports/${auditData.id}_speed.pdf`}
                    className="p-2 border border-border-subtle rounded-lg text-text-muted hover:text-accent hover:border-accent transition-colors"
                    title="Download PDF"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>
      )}

      {/* ── SEO DEEP DIVE ────────────────────────────────────────────────── */}
      {status === "complete" && viewingDetails === "seo" && auditData?.seo && (
        <motion.div
          key="details-seo"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="w-full"
        >
          <button
            onClick={() => setViewingDetails(null)}
            className="flex items-center gap-2 text-sm font-medium text-text-muted mb-6"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="flex items-center justify-between mb-8 pb-6 border-b border-border-subtle">
            <h2 className="text-2xl font-semibold">Technical SEO Scan</h2>
            <div className="text-4xl font-bold text-pass">
              {auditData.seo.seo_score || "N/A"}
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4 mb-10">
            <CircularProgress
              value={parseInt(auditData.seo.seo_score) || 0}
              label="SEO Health"
              colorClass="text-pass"
            />
          </div>

          <div className="space-y-3">
            {(auditData.seo.seo_tests || []).map((test: any) => (
              <div
                key={test.title}
                className="flex items-start gap-4 p-5 bg-bg-card border border-border-subtle rounded-xl"
              >
                {test.status === "pass" || test.status === "check" ? (
                  <CheckCircle className="text-pass shrink-0 mt-0.5" />
                ) : test.status === "warning" ? (
                  <AlertCircle className="text-warn shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="text-fail shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-medium text-text-main capitalize">
                    {test.title}
                  </div>
                  <div className="text-text-muted text-sm mt-1">
                    {test.content || "Test evaluated on the target URL."}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── SPEED DEEP DIVE ──────────────────────────────────────────────── */}
      {status === "complete" &&
        viewingDetails === "speed" &&
        auditData?.speed && (
          <motion.div
            key="details-speed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full"
          >
            <button
              onClick={() => setViewingDetails(null)}
              className="flex items-center gap-2 text-sm font-medium text-text-muted mb-6"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <div className="flex items-center justify-between mb-8 pb-6 border-b border-border-subtle">
              <h2 className="text-2xl font-semibold">Performance Audit</h2>
              <div className="text-4xl font-bold text-pass">
                {auditData.speed.mobile?.perf_score || auditData.speed.perf_score || "N/A"}
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4 mb-10">
              <div className="p-4 bg-bg-card border border-border-subtle rounded-xl text-center">
                <div className="text-xs text-text-muted uppercase font-bold mb-1">
                  FCP
                </div>
                <div className="text-xl font-bold">
                  {auditData.speed.mobile?.fcp || auditData.speed.metrics?.fcp || "N/A"}
                </div>
              </div>
              <div className="p-4 bg-bg-card border border-border-subtle rounded-xl text-center">
                <div className="text-xs text-text-muted uppercase font-bold mb-1">
                  LCP
                </div>
                <div className="text-xl font-bold">
                  {auditData.speed.mobile?.lcp || auditData.speed.metrics?.lcp || "N/A"}
                </div>
              </div>
              <div className="p-4 bg-bg-card border border-border-subtle rounded-xl text-center">
                <div className="text-xs text-text-muted uppercase font-bold mb-1">
                  CLS
                </div>
                <div className="text-xl font-bold">
                  {auditData.speed.mobile?.cls || auditData.speed.metrics?.cls || "N/A"}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {(auditData.speed.mobile?.speed_tests || auditData.speed.speed_tests || []).map((test: any) => (
                <div
                  key={test.title}
                  className="flex items-start gap-4 p-5 bg-bg-card border border-border-subtle rounded-xl"
                >
                  {test.status === "pass" ? (
                    <CheckCircle className="text-pass shrink-0 mt-0.5" />
                  ) : test.status === "warning" ? (
                    <AlertCircle className="text-warn shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="text-fail shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className="font-medium text-text-main capitalize">
                      {test.title}
                    </div>
                    <div className="text-text-muted text-sm mt-1">
                      {test.content
                        ?.replace(/\[Learn more\]\(.*\)/, "")
                        .trim() ||
                        "Optimization test for page loading performance."}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
    </AnimatePresence>
  );
}

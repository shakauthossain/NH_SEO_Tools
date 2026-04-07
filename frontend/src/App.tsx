import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, History } from "lucide-react";
import {
  useNavigate,
  useLocation,
  Link,
  Routes,
  Route,
} from "react-router-dom";

import api, { logout, isAuthenticated } from "./api";
import AuthModal from "./components/AuthModal";
import HistoryPanel from "./components/HistoryPanel";
import type { HistoryItem } from "./components/HistoryPanel";
import AdminPage from "./pages/AdminPage";
import BulkAuditPage from "./pages/BulkAuditPage";
import AnalyzePage from "./pages/AnalyzePage";
import type { AnalysisType, Status } from "./pages/AnalyzePage";

const PROGRESS_STEP_COUNT = 5;
const APP_TITLE = import.meta.env.VITE_APP_TITLE || "NH SEO Tools";

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  // ── Shared state ──────────────────────────────────────────────────────────
  const [url, setUrl] = useState("");
  const [analysisType, setAnalysisType] = useState<AnalysisType>("both");
  const [status, setStatus] = useState<Status>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [auditData, setAuditData] = useState<any>(null);
  const [viewingDetails, setViewingDetails] = useState<"seo" | "speed" | null>(
    null,
  );
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated());
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // ── Effects ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (isLoggedIn) fetchHistory();
  }, [isLoggedIn]);

  useEffect(() => {
    const matchReport = location.pathname.match(/^\/analyze\/(.+)\/([^/]+)$/);
    if (matchReport) {
      const domain = matchReport[1];
      const reportId = matchReport[2];
      if (!auditData || auditData.id !== reportId) {
        loadReport(reportId, domain);
      }
    } else if (location.pathname === "/" || location.pathname === "") {
      if (status === "complete" && auditData) {
        resetState();
      }
    }
  }, [location.pathname]);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const fetchHistory = async () => {
    try {
      const response = await api.get("/me/audits");
      setHistory(
        response.data.map((a: any) => ({
          id: a.report_id,
          url: a.url,
          date: new Date(a.created_at).toLocaleDateString(),
          type: "both" as AnalysisType,
          seoGrade: a.seo_score,
          speedGrade: a.speed_score,
        })),
      );
    } catch {
      console.error("Failed to fetch history");
    }
  };

  const loadReport = async (reportId: string, domain: string) => {
    setStatus("analyzing");
    try {
      const response = await api.get(`/audits/${reportId}`);
      setAuditData(response.data);
      setUrl(response.data.url);
      setStatus("complete");
      document.title = `SEO Audit: ${domain}`;
    } catch {
      console.error("Failed to load report");
      setStatus("idle");
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setStatus("analyzing");
    setActiveStep(0);

    // Animate progress steps
    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev < PROGRESS_STEP_COUNT - 1) return prev + 1;
        clearInterval(interval);
        return prev;
      });
    }, 1800);

    try {
      const response = await api.post("/analyze", {
        url,
        report_type: analysisType,
      });
      clearInterval(interval);
      const domain = url
        .replace(/^(?:https?:\/\/)?(?:www\.)?/i, "")
        .split("/")[0];
      setAuditData(response.data);
      setStatus("complete");
      navigate(`/analyze/${domain}/${response.data.id}`);
      if (isLoggedIn) fetchHistory();
    } catch (err) {
      clearInterval(interval);
      console.error("Analysis failed", err);
      setStatus("idle");
    }
  };

  const resetState = () => {
    setStatus("idle");
    setUrl("");
    setViewingDetails(null);
    setActiveStep(0);
    setAuditData(null);
    document.title = APP_TITLE;
  };

  const reset = () => {
    resetState();
    navigate("/");
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-bg-main text-text-main font-sans selection:bg-border-focus overflow-hidden flex flex-col">
      {/* Auth modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onSuccess={() => {
          setIsAuthModalOpen(false);
          setIsLoggedIn(true);
        }}
      />

      {/* Header */}
      <header className="flex-none flex items-center justify-between px-6 py-4 border-b border-border-subtle bg-bg-main">
        <div className="flex items-center gap-6">
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={reset}
          >
            <div className="w-8 h-8 bg-accent rounded-md flex items-center justify-center">
              <Activity className="w-5 h-5 text-accent-fg" />
            </div>
            <h1 className="text-lg font-semibold tracking-tight">
              {APP_TITLE}
            </h1>
          </div>

          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                location.pathname === "/" ||
                location.pathname.startsWith("/analyze")
                  ? "bg-bg-hover text-text-main"
                  : "text-text-muted hover:text-text-main"
              }`}
            >
              Analyze
            </Link>
            <Link
              to="/bulk-audit"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                location.pathname.startsWith("/bulk-audit")
                  ? "bg-bg-hover text-text-main"
                  : "text-text-muted hover:text-text-main"
              }`}
            >
              Bulk Audit
            </Link>
            <Link
              to="/admin"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                location.pathname === "/admin"
                  ? "bg-bg-hover text-text-main"
                  : "text-text-muted hover:text-text-main"
              }`}
            >
              Admin
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsHistoryOpen(!isHistoryOpen)}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-bg-hover transition-colors rounded-md text-text-muted"
          >
            <History className="w-4 h-4" />
          </button>

          {!isLoggedIn ? (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="bg-accent text-accent-fg px-4 py-1.5 rounded-md text-sm font-medium hover:bg-black/90 transition-colors"
            >
              Sign In
            </button>
          ) : (
            <button
              onClick={() => {
                logout();
                setIsLoggedIn(false);
                setHistory([]);
              }}
              className="text-text-muted hover:text-text-main text-sm font-medium"
            >
              Sign Out
            </button>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto relative">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <AnimatePresence mode="wait">
            <Routes
              location={location}
              key={location.pathname.split("/")[1] || "/"}
            >
              <Route path="/admin" element={<AdminPage />} />

              <Route
                path="/bulk-audit/*"
                element={
                  <BulkAuditPage
                    isLoggedIn={isLoggedIn}
                    onAuthRequired={() => setIsAuthModalOpen(true)}
                    onJobComplete={fetchHistory}
                  />
                }
              />

              <Route
                path="*"
                element={
                  <AnalyzePage
                    url={url}
                    setUrl={setUrl}
                    analysisType={analysisType}
                    setAnalysisType={setAnalysisType}
                    status={status}
                    activeStep={activeStep}
                    auditData={auditData}
                    viewingDetails={viewingDetails}
                    setViewingDetails={setViewingDetails}
                    isLoggedIn={isLoggedIn}
                    history={history}
                    onAnalyze={handleAnalyze}
                    onReset={reset}
                  />
                }
              />
            </Routes>
          </AnimatePresence>
        </div>
      </main>

      {/* History side panel */}
      <HistoryPanel
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        isLoggedIn={isLoggedIn}
        onItemClick={(item) => {
          const domain = item.url
            .replace(/^(?:https?:\/\/)?(?:www\.)?/i, "")
            .split("/")[0];
          navigate(`/analyze/${domain}/${item.id}`);
          setIsHistoryOpen(false);
        }}
      />
    </div>
  );
}

import React, { useState, useEffect } from "react";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useTransform,
  animate,
} from "framer-motion";
import {
  Search,
  Zap,
  Download,
  ExternalLink,
  Activity,
  Globe,
  CheckCircle2,
  ChevronRight,
  History,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Loader2,
  Lock,
  UserPlus,
  FileUp,
} from "lucide-react";
import api, { setAuthToken, logout, isAuthenticated } from "./api";
import {
  useNavigate,
  useLocation,
  Link,
  Routes,
  Route,
} from "react-router-dom";

type AnalysisType = "seo" | "speed" | "both";
type Status = "idle" | "analyzing" | "complete";

interface HistoryItem {
  id: string;
  url: string;
  date: string;
  type: AnalysisType;
  seoGrade?: string;
  speedGrade?: string;
}

const PROGRESS_STEPS = [
  "Connecting to server",
  "Fetching performance metrics",
  "Analyzing core web vitals",
  "Evaluating content structure",
  "Compiling report",
];

function AnimatedCounter({
  value,
  duration = 1.5,
}: {
  value: number;
  duration?: number;
}) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, Math.round);

  useEffect(() => {
    const animation = animate(count, value, { duration });
    return animation.stop;
  }, [value, duration, count]);

  return <motion.span>{rounded}</motion.span>;
}

function CircularProgress({
  value,
  label,
  colorClass,
}: {
  value: number;
  label: string;
  colorClass: string;
}) {
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-bg-card border border-border-subtle rounded-xl">
      <div className="relative w-20 h-20 mb-4">
        <svg
          className="w-full h-full transform -rotate-90"
          viewBox="0 0 100 100"
        >
          <circle
            className="text-border-subtle"
            strokeWidth="6"
            stroke="currentColor"
            fill="transparent"
            r="40"
            cx="50"
            cy="50"
          />
          <motion.circle
            className={colorClass}
            strokeWidth="6"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
            r="40"
            cx="50"
            cy="50"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-semibold text-text-main">
            <AnimatedCounter value={value} />
          </span>
        </div>
      </div>
      <span className="text-sm text-text-muted font-medium text-center">
        {label}
      </span>
    </div>
  );
}

function AuthModal({
  isOpen,
  onSuccess,
}: {
  isOpen: boolean;
  onSuccess: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api.post(
        `/token?email=${email}&password=${password}`,
      );
      setAuthToken(response.data.access_token);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md bg-bg-main border border-border-subtle p-8 rounded-2xl shadow-2xl"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
            <Lock className="w-5 h-5 text-accent-fg" />
          </div>
          <h2 className="text-2xl font-semibold text-text-main">
            Welcome Back
          </h2>
        </div>
        <p className="text-text-muted mb-8 text-sm">
          Please log in with your credentials to access full audit reports and
          bulk testing.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-text-muted mb-2 uppercase tracking-wider">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-bg-card border border-border-subtle focus:border-border-focus outline-none p-3 rounded-lg text-text-main"
              placeholder="name@company.com"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-muted mb-2 uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-bg-card border border-border-subtle focus:border-border-focus outline-none p-3 rounded-lg text-text-main"
              placeholder="••••••••"
              required
            />
          </div>
          {error && <p className="text-fail text-xs mt-2">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent text-accent-fg py-3 rounded-lg font-semibold hover:bg-black/90 transition-all flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Sign In"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [url, setUrl] = useState("");
  const [analysisType, setAnalysisType] = useState<AnalysisType>("both");
  const [status, setStatus] = useState<Status>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [viewingDetails, setViewingDetails] = useState<"seo" | "speed" | null>(
    null,
  );
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isBulkMode, setIsBulkMode] = useState(false);
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated());

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [auditData, setAuditData] = useState<any>(null);

  // Admin states
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPass, setAdminPass] = useState("");
  const [adminStatus, setAdminStatus] = useState("");

  // Bulk states
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [bulkJobId, setBulkJobId] = useState<number | null>(null);
  const [bulkStatus, setBulkStatus] = useState<any>(null);

  useEffect(() => {
    if (isLoggedIn) {
      fetchHistory();
    }
  }, [isLoggedIn]);

  useEffect(() => {
    const match = location.pathname.match(/^\/analyze\/(.+)\/([^/]+)$/);
    if (match) {
      const domain = match[1];
      const reportId = match[2];
      if (!auditData || auditData.id !== reportId) {
        loadReport(reportId, domain);
      }
    } else if (location.pathname === "/" || location.pathname === "") {
      if (status === "complete" && auditData) {
        resetState();
      }
    }

    const matchBulk = location.pathname.match(/^\/bulk-audit\/(.+)$/);
    if (matchBulk) {
      const jobId = Number(matchBulk[1]);
      if (bulkJobId !== jobId) {
        setBulkJobId(jobId);
        pollBulkStatus(jobId);
      }
    }
  }, [location.pathname]);

  const loadReport = async (reportId: string, domain: string) => {
    setStatus("analyzing");
    setIsBulkMode(false);
    setIsAdminMode(false);
    try {
      const response = await api.get(`/audits/${reportId}`);
      setAuditData(response.data);
      setUrl(response.data.url);
      setStatus("complete");
      document.title = `SEO Audit: ${domain}`;
    } catch (e) {
      console.error(e);
      setStatus("idle");
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await api.get("/me/audits");
      setHistory(
        response.data.map((a: any) => ({
          id: a.report_id,
          url: a.url,
          date: new Date(a.created_at).toLocaleDateString(),
          type: "both",
          seoGrade: a.seo_score,
          speedGrade: a.speed_score,
        })),
      );
    } catch (err) {
      console.error("Failed to fetch history");
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setStatus("analyzing");
    setActiveStep(0);

    try {
      const response = await api.post("/analyze", {
        url,
        report_type: analysisType,
      });
      const domain = url
        .replace(/^(?:https?:\/\/)?(?:www\.)?/i, "")
        .split("/")[0];
      navigate(`/analyze/${domain}/${response.data.id}`);
      if (isLoggedIn) fetchHistory();
    } catch (err) {
      console.error("Analysis failed");
      setStatus("idle");
    }
  };

  const handleBulkUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkFile) return;
    if (!isLoggedIn) {
      setIsAuthModalOpen(true);
      return;
    }

    const formData = new FormData();
    formData.append("file", bulkFile);

    try {
      const response = await api.post("/analyze/bulk", formData);
      setBulkJobId(response.data.job_id);
      navigate(`/bulk-audit/${response.data.job_id}`);
      setIsBulkMode(false);
      pollBulkStatus(response.data.job_id);
    } catch (err) {
      console.error("Bulk upload failed");
    }
  };

  const pollBulkStatus = async (jobId: number) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/bulk/status/${jobId}`);
        setBulkStatus(response.data);
        if (
          response.data.status === "completed" ||
          response.data.status === "failed"
        ) {
          clearInterval(interval);
          fetchHistory();
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 5000);
  };

  const handleAdminCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Prompt for admin basic auth (simplified for this task)
      const user = prompt("Admin User?");
      const pass = prompt("Admin Pass?");

      await api.post(
        `/admin/create-user?email=${adminEmail}&password=${adminPass}`,
        {},
        {
          auth: { username: user || "", password: pass || "" },
        },
      );
      setAdminStatus(`Successfully created user ${adminEmail}`);
      setAdminEmail("");
      setAdminPass("");
    } catch (err) {
      setAdminStatus("Admin operation failed");
    }
  };

  const resetState = () => {
    setStatus("idle");
    setUrl("");
    setViewingDetails(null);
    setActiveStep(0);
    setAuditData(null);
    document.title = "Antigravity SEO";
  };

  const reset = () => {
    resetState();
    navigate("/");
  };

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

  return (
    <div className="min-h-screen bg-bg-main text-text-main font-sans selection:bg-border-focus overflow-hidden flex flex-col">
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
              Antigravity SEO
            </h1>
          </div>

          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${location.pathname === "/" || location.pathname.startsWith("/analyze") ? "bg-bg-hover text-text-main" : "text-text-muted hover:text-text-main"}`}
            >
              Analyze
            </Link>
            <Link
              to="/bulk-audit"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${location.pathname.startsWith("/bulk-audit") ? "bg-bg-hover text-text-main" : "text-text-muted hover:text-text-main"}`}
            >
              Bulk Audit
            </Link>
            <Link
              to="/admin"
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${location.pathname === "/admin" ? "bg-bg-hover text-text-main" : "text-text-muted hover:text-text-main"}`}
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
              }}
              className="text-text-muted hover:text-text-main text-sm font-medium"
            >
              Sign Out
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <AnimatePresence mode="wait">
            <Routes
              location={location}
              {...({ key: location.pathname.split("/")[1] || "/" } as any)}
            >
              {/* ADMIN MODE */}
              <Route
                path="/admin"
                element={
                  <motion.div
                    key="admin"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="max-w-md"
                  >
                    <h2 className="text-3xl font-semibold mb-6 flex items-center gap-3">
                      <UserPlus className="w-8 h-8 text-accent" />
                      User Management
                    </h2>
                    <form
                      onSubmit={handleAdminCreate}
                      className="space-y-4 bg-bg-card p-6 border border-border-subtle rounded-xl"
                    >
                      <p className="text-sm text-text-muted mb-4">
                        Create internal user accounts for client access.
                      </p>
                      <input
                        type="email"
                        placeholder="New User Email"
                        value={adminEmail}
                        onChange={(e) => setAdminEmail(e.target.value)}
                        className="w-full bg-bg-main border border-border-subtle p-3 rounded-lg outline-none focus:border-border-focus"
                      />
                      <input
                        type="password"
                        placeholder="Temporary Password"
                        value={adminPass}
                        onChange={(e) => setAdminPass(e.target.value)}
                        className="w-full bg-bg-main border border-border-subtle p-3 rounded-lg outline-none focus:border-border-focus"
                      />
                      <button className="w-full bg-accent text-accent-fg py-3 rounded-lg font-medium">
                        Create User
                      </button>
                      {adminStatus && (
                        <p className="text-xs text-accent mt-2">
                          {adminStatus}
                        </p>
                      )}
                    </form>
                  </motion.div>
                }
              />

              {/* BULK MODE */}
              <Route
                path="/bulk-audit/*"
                element={
                  <motion.div
                    key="bulk"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                  >
                    <h2 className="text-3xl font-semibold mb-2">
                      Bulk Analysis
                    </h2>
                    <p className="text-text-muted mb-8 italic">
                      Upload a CSV/XLSX file with at least one "URL" column.
                    </p>

                    {!bulkJobId ? (
                      <form onSubmit={handleBulkUpload} className="space-y-6">
                        <div className="border-2 border-dashed border-border-subtle hover:border-accent rounded-2xl p-12 flex flex-col items-center justify-center transition-colors group cursor-pointer relative">
                          <input
                            type="file"
                            accept=".csv,.xlsx"
                            onChange={(e) =>
                              setBulkFile(e.target.files?.[0] || null)
                            }
                            className="absolute inset-0 opacity-0 cursor-pointer"
                          />
                          <FileUp className="w-12 h-12 text-text-muted group-hover:text-accent mb-4 transition-colors" />
                          <p className="text-lg font-medium text-text-main">
                            {bulkFile
                              ? bulkFile.name
                              : "Click or Drag File to Upload"}
                          </p>
                          <p className="text-sm text-text-muted mt-2">
                            Supports .csv and .xlsx files up to 5MB
                          </p>
                        </div>
                        {bulkFile && (
                          <button className="w-full bg-accent text-accent-fg py-4 rounded-xl font-semibold flex items-center justify-center gap-2">
                            Start Batch Process{" "}
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        )}
                      </form>
                    ) : (
                      <div className="bg-bg-card border border-border-subtle p-8 rounded-2xl relative overflow-hidden z-0">
                        <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-accent/10 opacity-60 z-[-1]"></div>
                        <div className="flex flex-col items-center justify-center py-6">
                          <div className="relative flex items-center justify-center mb-6">
                            {bulkStatus?.status !== "completed" && (
                              <motion.div
                                animate={{ rotate: 360 }}
                                transition={{
                                  repeat: Infinity,
                                  duration: 2,
                                  ease: "linear",
                                }}
                                className="absolute -inset-4 border border-accent/40 border-t-accent rounded-full"
                              />
                            )}
                            <div className="w-16 h-16 bg-bg-main rounded-full flex items-center justify-center shadow-lg border border-border-subtle z-10">
                              {bulkStatus?.status === "completed" ? (
                                <CheckCircle2 className="w-8 h-8 text-pass" />
                              ) : (
                                <Activity className="w-8 h-8 text-accent animate-pulse" />
                              )}
                            </div>
                          </div>

                          <h3 className="text-2xl font-bold text-text-main capitalize mb-2">
                            {bulkStatus?.status === "completed"
                              ? "Processing Complete"
                              : "Analyzing Batch..."}
                          </h3>
                          <p className="text-text-muted text-sm mb-8 text-center max-w-sm">
                            {bulkStatus?.status === "completed"
                              ? "All URLs have been successfully audited."
                              : "We are crawling your URLs and generating comprehensive core web vitals and SEO data."}
                          </p>

                          <div className="w-full max-w-md">
                            <div className="flex justify-between text-xs font-bold uppercase text-text-muted mb-2">
                              <span>Progress</span>
                              <span>
                                {bulkStatus?.status === "completed"
                                  ? "100"
                                  : "50"}
                                %
                              </span>
                            </div>
                            <div className="relative w-full h-3 bg-bg-main border border-border-subtle rounded-full overflow-hidden shadow-inner mb-8">
                              <motion.div
                                className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-accent/80 to-accent"
                                initial={{ width: "5%" }}
                                animate={{
                                  width:
                                    bulkStatus?.status === "completed"
                                      ? "100%"
                                      : "50%",
                                }}
                                transition={{
                                  duration: 0.8,
                                  ease: "easeInOut",
                                }}
                              />
                              {bulkStatus?.status !== "completed" && (
                                <motion.div
                                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                                  initial={{ x: "-100%" }}
                                  animate={{ x: "100%" }}
                                  transition={{
                                    repeat: Infinity,
                                    duration: 1.5,
                                    ease: "linear",
                                  }}
                                />
                              )}
                            </div>
                          </div>

                          {bulkStatus?.output_filename && (
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.2 }}
                              className="flex flex-col items-center gap-3"
                            >
                              <a
                                href={`http://localhost:8000/reports/${bulkStatus.output_filename}`}
                                className="inline-flex items-center justify-center gap-3 bg-pass hover:bg-pass/90 text-bg-main px-8 py-3.5 rounded-xl font-bold shadow-lg transition-transform hover:-translate-y-0.5"
                              >
                                <Download className="w-5 h-5" /> Download
                                Results CSV
                              </a>
                              <button
                                onClick={() => {
                                  setBulkJobId(null);
                                  setBulkFile(null);
                                  setBulkStatus(null);
                                  navigate("/bulk-audit");
                                }}
                                className="inline-flex items-center justify-center gap-3 bg-transparent border-2 border-border-focus/40 hover:border-accent text-text-main px-8 py-3.5 rounded-xl font-bold shadow-sm transition-all hover:bg-accent/5 hover:-translate-y-0.5"
                              >
                                Run Another Batch
                              </button>
                            </motion.div>
                          )}
                        </div>
                      </div>
                    )}
                  </motion.div>
                }
              />

              {/* SINGLE MODE */}
              <Route
                path="*"
                element={
                  <AnimatePresence mode="wait">
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
                            Enter a URL to analyze Technical SEO, Page Speed,
                            and Core Web Vitals using the premium RankMath
                            engine.
                          </p>
                        </div>
                        <form
                          onSubmit={handleAnalyze}
                          className="w-full max-w-2xl space-y-6"
                        >
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
                              {["seo", "both", "speed"].map((type) => (
                                <button
                                  key={type}
                                  type="button"
                                  onClick={() =>
                                    setAnalysisType(type as AnalysisType)
                                  }
                                  className={`relative px-6 py-2 text-sm font-medium transition-colors flex items-center gap-2 z-10 rounded-md ${analysisType === type ? "text-accent-fg" : "text-text-muted hover:text-text-main"}`}
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

                        {/* Recent Audits (Inline on Landing Page) */}
                        {isLoggedIn && history.length > 0 && (
                          <div className="mt-16 w-full max-w-4xl">
                            <h3 className="text-xl font-semibold mb-6 flex items-center gap-2 text-text-main">
                              <History className="w-5 h-5 text-text-muted" />{" "}
                              Recent Audits
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {history.slice(0, 6).map((item) => (
                                <div
                                  key={`inline-${item.id}`}
                                  className="p-5 rounded-xl bg-bg-card border border-border-subtle hover:border-border-focus cursor-pointer transition-colors"
                                  onClick={() => {
                                    const domain = item.url
                                      .replace(
                                        /^(?:https?:\/\/)?(?:www\.)?/i,
                                        "",
                                      )
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

                    {status === "analyzing" && (
                      <motion.div
                        key="analyzing"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
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
                              className={`flex items-center gap-4 p-3 rounded-lg ${index <= activeStep ? "opacity-100" : "opacity-30"}`}
                            >
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${index < activeStep ? "bg-pass text-bg-main" : "border-2 border-accent"}`}
                              >
                                {index < activeStep ? (
                                  <CheckCircle2 className="w-4 h-4" />
                                ) : (
                                  index + 1
                                )}
                              </div>
                              <span className="text-base text-text-main">
                                {step}
                              </span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}

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
                            onClick={reset}
                            className="px-4 py-2 border border-border-subtle hover:border-border-focus rounded-lg text-sm font-medium transition-colors"
                          >
                            Reset
                          </button>
                        </div>

                        <div className="grid md:grid-cols-2 gap-6">
                          {auditData?.seo && (
                            <motion.div
                              variants={itemVariants}
                              className="bg-bg-card border border-border-subtle rounded-xl p-6 hover:border-border-focus flex flex-col"
                            >
                              <div className="flex justify-between items-start mb-8">
                                <div className="flex items-center gap-3">
                                  <Search className="w-5 h-5 text-accent" />
                                  <h3 className="text-lg font-semibold">
                                    SEO Engine
                                  </h3>
                                </div>
                                <div className="text-4xl font-bold text-pass">
                                  {auditData.seo.seo_score || "N/A"}
                                </div>
                              </div>
                              <div className="space-y-3 mb-8 flex-1">
                                {(auditData.seo.seo_tests || [])
                                  .slice(0, 3)
                                  .map((test: any) => (
                                    <div
                                      key={test.title}
                                      className="flex justify-between items-center py-2 border-b border-border-subtle"
                                    >
                                      <span className="text-text-muted text-sm capitalize">
                                        {test.title}
                                      </span>
                                      <span
                                        className={`text-sm font-bold ${test.status === "check" ? "text-pass" : "text-warn"}`}
                                      >
                                        {test.status === "check"
                                          ? "PASS"
                                          : "WARN"}
                                      </span>
                                    </div>
                                  ))}
                              </div>
                              <div className="flex gap-3">
                                <button
                                  onClick={() => setViewingDetails("seo")}
                                  className="flex-1 bg-bg-hover border border-border-subtle py-2 rounded-lg text-sm font-medium"
                                >
                                  Deep Dive
                                </button>
                                <a
                                  href={`http://localhost:8000/reports/${auditData.id}_seo.pdf`}
                                  className="p-2 border border-border-subtle rounded-lg"
                                >
                                  <Download className="w-4 h-4" />
                                </a>
                              </div>
                            </motion.div>
                          )}
                          {auditData?.speed && (
                            <motion.div
                              variants={itemVariants}
                              className="bg-bg-card border border-border-subtle rounded-xl p-6 hover:border-border-focus flex flex-col"
                            >
                              <div className="flex justify-between items-start mb-8">
                                <div className="flex items-center gap-3">
                                  <Zap className="w-5 h-5 text-warn" />
                                  <h3 className="text-lg font-semibold">
                                    Page Experience
                                  </h3>
                                </div>
                                <div className="text-4xl font-bold text-pass">
                                  {auditData.speed.perf_score || "N/A"}
                                </div>
                              </div>
                              <div className="space-y-3 mb-8 flex-1">
                                <div className="flex justify-between py-2 border-b border-border-subtle">
                                  <span className="text-text-muted text-sm">
                                    FCP
                                  </span>
                                  <span className="text-sm font-bold">
                                    {auditData.speed.metrics.fcp}
                                  </span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-border-subtle">
                                  <span className="text-text-muted text-sm">
                                    LCP
                                  </span>
                                  <span className="text-sm font-bold">
                                    {auditData.speed.metrics.lcp}
                                  </span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-border-subtle">
                                  <span className="text-text-muted text-sm">
                                    CLS
                                  </span>
                                  <span className="text-sm font-bold">
                                    {auditData.speed.metrics.cls}
                                  </span>
                                </div>
                              </div>
                              <div className="flex gap-3">
                                <button
                                  onClick={() => setViewingDetails("speed")}
                                  className="flex-1 bg-bg-hover border border-border-subtle py-2 rounded-lg text-sm font-medium"
                                >
                                  Metric Breakdown
                                </button>
                                <a
                                  href={`http://localhost:8000/reports/${auditData.id}_speed.pdf`}
                                  className="p-2 border border-border-subtle rounded-lg"
                                >
                                  <Download className="w-4 h-4" />
                                </a>
                              </div>
                            </motion.div>
                          )}
                        </div>
                      </motion.div>
                    )}

                    {/* DETAILS VIEWS */}
                    {viewingDetails === "seo" && auditData?.seo && (
                      <motion.div
                        key="details-seo"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="w-full"
                      >
                        <button
                          onClick={() => setViewingDetails(null)}
                          className="flex items-center gap-2 text-sm font-medium text-text-muted mb-6"
                        >
                          <ArrowLeft className="w-4 h-4" /> Back
                        </button>
                        <div className="flex items-center justify-between mb-8 pb-6 border-b border-border-subtle">
                          <h2 className="text-2xl font-semibold">
                            Technical SEO Scan
                          </h2>
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
                              {test.status === "check" ? (
                                <CheckCircle className="text-pass" />
                              ) : (
                                <AlertCircle className="text-warn" />
                              )}
                              <div>
                                <div className="font-medium text-text-main capitalize">
                                  {test.title}
                                </div>
                                <div className="text-text-muted text-sm">
                                  Test passed successfully on the target URL.
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}

                    {viewingDetails === "speed" && auditData?.speed && (
                      <motion.div
                        key="details-speed"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="w-full"
                      >
                        <button
                          onClick={() => setViewingDetails(null)}
                          className="flex items-center gap-2 text-sm font-medium text-text-muted mb-6"
                        >
                          <ArrowLeft className="w-4 h-4" /> Back
                        </button>
                        <div className="flex items-center justify-between mb-8 pb-6 border-b border-border-subtle">
                          <h2 className="text-2xl font-semibold">
                            Performance Audit
                          </h2>
                          <div className="text-4xl font-bold text-pass">
                            {auditData.speed.perf_score || "N/A"}
                          </div>
                        </div>
                        <div className="grid md:grid-cols-3 gap-4 mb-10">
                          <div className="p-4 bg-bg-card border border-border-subtle rounded-xl text-center">
                            <div className="text-xs text-text-muted uppercase font-bold mb-1">
                              FCP
                            </div>
                            <div className="text-xl font-bold">
                              {auditData.speed.metrics?.fcp || "N/A"}
                            </div>
                          </div>
                          <div className="p-4 bg-bg-card border border-border-subtle rounded-xl text-center">
                            <div className="text-xs text-text-muted uppercase font-bold mb-1">
                              LCP
                            </div>
                            <div className="text-xl font-bold">
                              {auditData.speed.metrics?.lcp || "N/A"}
                            </div>
                          </div>
                          <div className="p-4 bg-bg-card border border-border-subtle rounded-xl text-center">
                            <div className="text-xs text-text-muted uppercase font-bold mb-1">
                              CLS
                            </div>
                            <div className="text-xl font-bold">
                              {auditData.speed.metrics?.cls || "N/A"}
                            </div>
                          </div>
                        </div>
                        <div className="space-y-3">
                          {(auditData.speed.speed_tests || []).map(
                            (test: any) => (
                              <div
                                key={test.title}
                                className="flex items-start gap-4 p-5 bg-bg-card border border-border-subtle rounded-xl"
                              >
                                {test.status === "check" ? (
                                  <CheckCircle className="text-pass" />
                                ) : (
                                  <AlertCircle className="text-warn" />
                                )}
                                <div className="flex-1">
                                  <div className="font-medium text-text-main capitalize">
                                    {test.title}
                                  </div>
                                  <div className="text-text-muted text-sm mt-1">
                                    {test.content?.replace(
                                      /\[Learn more\]\(.*\)/,
                                      "",
                                    ) ||
                                      "Optimization test for page loading performance."}
                                  </div>
                                </div>
                              </div>
                            ),
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                }
              />
            </Routes>
          </AnimatePresence>
        </div>
      </main>

      {/* History Side Panel (Now Live) */}
      <AnimatePresence>
        {isHistoryOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsHistoryOpen(false)}
              className="fixed inset-0 bg-black/40 z-90"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              className="fixed top-0 right-0 bottom-0 w-full max-w-sm bg-bg-main border-l border-border-subtle z-100 flex flex-col shadow-2xl"
            >
              <div className="p-5 border-b border-border-subtle flex items-center justify-between">
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <History className="w-4 h-4 text-text-muted" />
                  Audit History
                </h2>
                <button
                  onClick={() => setIsHistoryOpen(false)}
                  className="p-1.5 rounded-md hover:bg-bg-hover"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3">
                {isLoggedIn ? (
                  history.map((item) => (
                    <div
                      key={item.id}
                      className="p-4 rounded-lg bg-bg-card border border-border-subtle hover:border-border-focus cursor-pointer transition-colors"
                      onClick={() => {
                        const domain = item.url
                          .replace(/^(?:https?:\/\/)?(?:www\.)?/i, "")
                          .split("/")[0];
                        navigate(`/analyze/${domain}/${item.id}`);
                        setIsHistoryOpen(false);
                      }}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <span className="font-medium text-sm truncate max-w-[150px]">
                          {item.url}
                        </span>
                        <span className="text-xs text-text-muted">
                          {item.date}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <span className="text-[10px] uppercase font-bold text-pass">
                          SEO: {item.seoGrade}
                        </span>
                        <span className="text-[10px] uppercase font-bold text-warn">
                          Speed: {item.speedGrade}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-10">
                    <p className="text-sm text-text-muted">
                      Please sign in to view history
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

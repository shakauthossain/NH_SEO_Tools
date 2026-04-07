import React, { useState } from "react";

import { API_BASE_URL as API_URL } from "../api";
import { motion } from "framer-motion";
import {
  FileUp,
  ArrowRight,
  Activity,
  CheckCircle2,
  Download,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../api";

interface BulkAuditPageProps {
  isLoggedIn: boolean;
  onAuthRequired: () => void;
  onJobComplete: () => void;
}

export default function BulkAuditPage({
  isLoggedIn,
  onAuthRequired,
  onJobComplete,
}: BulkAuditPageProps) {
  const navigate = useNavigate();
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [bulkJobId, setBulkJobId] = useState<number | null>(null);
  const [bulkStatus, setBulkStatus] = useState<any>(null);

  const pollBulkStatus = (jobId: number) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/bulk/status/${jobId}`);
        setBulkStatus(response.data);
        if (
          response.data.status === "completed" ||
          response.data.status === "failed"
        ) {
          clearInterval(interval);
          onJobComplete();
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 5000);
  };

  const handleBulkUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkFile) return;
    if (!isLoggedIn) {
      onAuthRequired();
      return;
    }

    const formData = new FormData();
    formData.append("file", bulkFile);

    try {
      const response = await api.post("/analyze/bulk", formData);
      const jobId = response.data.job_id;
      setBulkJobId(jobId);
      navigate(`/bulk-audit/${jobId}`);
      pollBulkStatus(jobId);
    } catch (err) {
      console.error("Bulk upload failed");
    }
  };

  return (
    <motion.div
      key="bulk"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
    >
      <h2 className="text-3xl font-semibold mb-2">Bulk Analysis</h2>
      <p className="text-text-muted mb-8 italic">
        Upload a CSV/XLSX file with at least one "URL" column.
      </p>

      {!bulkJobId ? (
        <form onSubmit={handleBulkUpload} className="space-y-6">
          <div className="border-2 border-dashed border-border-subtle hover:border-accent rounded-2xl p-12 flex flex-col items-center justify-center transition-colors group cursor-pointer relative">
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={(e) => setBulkFile(e.target.files?.[0] || null)}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            <FileUp className="w-12 h-12 text-text-muted group-hover:text-accent mb-4 transition-colors" />
            <p className="text-lg font-medium text-text-main">
              {bulkFile ? bulkFile.name : "Click or Drag File to Upload"}
            </p>
            <p className="text-sm text-text-muted mt-2">
              Supports .csv and .xlsx files up to 5MB
            </p>
          </div>
          {bulkFile && (
            <button
              type="submit"
              className="w-full bg-accent text-accent-fg py-4 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              Start Batch Process <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </form>
      ) : (
        <div className="bg-bg-card border border-border-subtle p-8 rounded-2xl relative overflow-hidden z-0">
          <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-accent/10 opacity-60 z-[-1]" />
          <div className="flex flex-col items-center justify-center py-6">
            {/* Spinner / check icon */}
            <div className="relative flex items-center justify-center mb-6">
              {bulkStatus?.status !== "completed" && (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
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

            {/* Progress bar */}
            <div className="w-full max-w-md">
              <div className="flex justify-between text-xs font-bold uppercase text-text-muted mb-2">
                <span>Progress</span>
                <span>
                  {bulkStatus?.status === "completed" 
                    ? "100" 
                    : Math.round(((bulkStatus?.processed_count || 0) / (bulkStatus?.total_count || 1)) * 100)}%
                </span>
              </div>
              <div className="relative w-full h-3 bg-bg-main border border-border-subtle rounded-full overflow-hidden shadow-inner mb-4">
                <motion.div
                  className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-accent/80 to-accent"
                  initial={{ width: "5%" }}
                  animate={{
                    width: bulkStatus?.status === "completed" 
                      ? "100%" 
                      : `${Math.max(5, ((bulkStatus?.processed_count || 0) / (bulkStatus?.total_count || 1)) * 100)}%`,
                  }}
                  transition={{ duration: 0.8, ease: "easeInOut" }}
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
              
              {/* Processed Count indicator */}
              <div className="text-center text-xs font-bold text-text-muted mb-8 tracking-widest uppercase opacity-70">
                {bulkStatus?.processed_count || 0} / {bulkStatus?.total_count || 0} Leads Completed
              </div>
            </div>

            {/* Download + reset */}
            {bulkStatus?.output_filename && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="flex flex-col items-center gap-3"
              >
                <a
                  href={`${API_URL}/reports/${bulkStatus.output_filename}`}
                  className="inline-flex items-center justify-center gap-3 bg-pass hover:bg-pass/90 text-bg-main px-8 py-3.5 rounded-xl font-bold shadow-lg transition-transform hover:-translate-y-0.5"
                >
                  <Download className="w-5 h-5" /> Download Results CSV
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
  );
}

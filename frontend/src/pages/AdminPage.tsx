import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lock,
  Loader2,
  Users,
  BarChart3,
  FileUp,
  UserPlus,
  Trash2,
} from "lucide-react";
import api from "../api";

export default function AdminPage() {
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPass, setAdminPass] = useState("");
  const [adminStatus, setAdminStatus] = useState("");
  const [isAdminAuthOpen, setIsAdminAuthOpen] = useState(false);
  const [adminAuthUser, setAdminAuthUser] = useState("");
  const [adminAuthPass, setAdminAuthPass] = useState("");
  const [adminAuthLoading, setAdminAuthLoading] = useState(false);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [adminStats, setAdminStats] = useState<any>(null);
  const [adminLoggedIn, setAdminLoggedIn] = useState(false);
  const [savedAdminCreds, setSavedAdminCreds] = useState<{
    user: string;
    pass: string;
  } | null>(null);

  const fetchAdminData = async (user: string, pass: string) => {
    try {
      const [usersRes, statsRes] = await Promise.all([
        api.get("/admin/users", { auth: { username: user, password: pass } }),
        api.get("/admin/stats", { auth: { username: user, password: pass } }),
      ]);
      setAdminUsers(usersRes.data);
      setAdminStats(statsRes.data);
    } catch (err) {
      console.error("Failed to fetch admin data");
    }
  };

  const handleAdminAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdminAuthLoading(true);
    try {
      await api.get("/admin/stats", {
        auth: { username: adminAuthUser, password: adminAuthPass },
      });
      setSavedAdminCreds({ user: adminAuthUser, pass: adminAuthPass });
      setAdminLoggedIn(true);
      setIsAdminAuthOpen(false);
      fetchAdminData(adminAuthUser, adminAuthPass);

      if (adminEmail && adminPass) {
        await api.post(
          `/admin/create-user?email=${adminEmail}&password=${adminPass}`,
          {},
          { auth: { username: adminAuthUser, password: adminAuthPass } },
        );
        setAdminStatus(`Successfully created user ${adminEmail}`);
        setAdminEmail("");
        setAdminPass("");
        fetchAdminData(adminAuthUser, adminAuthPass);
      }
    } catch (err) {
      setAdminStatus("Invalid admin credentials");
    } finally {
      setAdminAuthLoading(false);
    }
  };

  const handleAdminCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminEmail || !adminPass) return;
    if (!savedAdminCreds) {
      setIsAdminAuthOpen(true);
      return;
    }
    try {
      await api.post(
        `/admin/create-user?email=${adminEmail}&password=${adminPass}`,
        {},
        {
          auth: {
            username: savedAdminCreds.user,
            password: savedAdminCreds.pass,
          },
        },
      );
      setAdminStatus(`Successfully created user ${adminEmail}`);
      setAdminEmail("");
      setAdminPass("");
      fetchAdminData(savedAdminCreds.user, savedAdminCreds.pass);
    } catch (err) {
      setAdminStatus("Admin operation failed");
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!savedAdminCreds) return;
    try {
      await api.delete(`/admin/users/${userId}`, {
        auth: {
          username: savedAdminCreds.user,
          password: savedAdminCreds.pass,
        },
      });
      fetchAdminData(savedAdminCreds.user, savedAdminCreds.pass);
    } catch (err) {
      setAdminStatus("Failed to delete user");
    }
  };

  return (
    <motion.div
      key="admin"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="w-full"
    >
      {/* Admin Auth Modal (for inline create-user action) */}
      <AnimatePresence>
        {isAdminAuthOpen && (
          <div className="fixed inset-0 z-100 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-bg-main border border-border-subtle p-8 rounded-2xl shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
                  <Lock className="w-5 h-5 text-accent-fg" />
                </div>
                <h2 className="text-2xl font-semibold text-text-main">
                  Admin Verification
                </h2>
              </div>
              <p className="text-text-muted mb-8 text-sm">
                Please enter your Super Admin credentials to authorize this
                action.
              </p>
              <form onSubmit={handleAdminAuthSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-2 uppercase tracking-wider">
                    Admin Username
                  </label>
                  <input
                    type="text"
                    value={adminAuthUser}
                    onChange={(e) => setAdminAuthUser(e.target.value)}
                    className="w-full bg-bg-card border border-border-subtle focus:border-border-focus outline-none p-3 rounded-lg text-text-main"
                    placeholder="admin@seo.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-2 uppercase tracking-wider">
                    Admin Password
                  </label>
                  <input
                    type="password"
                    value={adminAuthPass}
                    onChange={(e) => setAdminAuthPass(e.target.value)}
                    className="w-full bg-bg-card border border-border-subtle focus:border-border-focus outline-none p-3 rounded-lg text-text-main"
                    placeholder="••••••••"
                    required
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsAdminAuthOpen(false);
                      setAdminAuthUser("");
                      setAdminAuthPass("");
                    }}
                    className="flex-1 border border-border-subtle py-3 rounded-lg font-medium text-text-muted hover:bg-bg-hover transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={adminAuthLoading}
                    className="flex-1 bg-accent text-accent-fg py-3 rounded-lg font-semibold hover:bg-black/90 transition-all flex items-center justify-center gap-2"
                  >
                    {adminAuthLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Authorize"
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {!adminLoggedIn ? (
        /* ── Login form ─────────────────────────────────────────────────── */
        <div className="max-w-md mx-auto">
          <h2 className="text-3xl font-semibold mb-6 flex items-center gap-3">
            <Lock className="w-8 h-8 text-accent" />
            Admin Panel
          </h2>
          <div className="bg-bg-card p-6 border border-border-subtle rounded-xl">
            <p className="text-sm text-text-muted mb-6">
              Please authenticate with Super Admin credentials to continue.
            </p>
            <form onSubmit={handleAdminAuthSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="Admin Email"
                value={adminAuthUser}
                onChange={(e) => setAdminAuthUser(e.target.value)}
                className="w-full bg-bg-main border border-border-subtle p-3 rounded-lg outline-none focus:border-border-focus"
                required
              />
              <input
                type="password"
                placeholder="Admin Password"
                value={adminAuthPass}
                onChange={(e) => setAdminAuthPass(e.target.value)}
                className="w-full bg-bg-main border border-border-subtle p-3 rounded-lg outline-none focus:border-border-focus"
                required
              />
              <button
                type="submit"
                disabled={adminAuthLoading}
                className="w-full bg-accent text-accent-fg py-3 rounded-lg font-semibold flex items-center justify-center gap-2"
              >
                {adminAuthLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  "Sign In as Admin"
                )}
              </button>
              {adminStatus && (
                <p className="text-xs text-red-400 mt-2">{adminStatus}</p>
              )}
            </form>
          </div>
        </div>
      ) : (
        /* ── Dashboard ──────────────────────────────────────────────────── */
        <div className="space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-semibold flex items-center gap-3">
              <Users className="w-8 h-8 text-accent" />
              Admin Dashboard
            </h2>
            <button
              onClick={() => {
                setAdminLoggedIn(false);
                setSavedAdminCreds(null);
                setAdminUsers([]);
                setAdminStats(null);
                setAdminAuthUser("");
                setAdminAuthPass("");
                setAdminStatus("");
              }}
              className="text-sm text-text-muted hover:text-text-main"
            >
              Sign Out Admin
            </button>
          </div>

          {/* Stats Cards */}
          {adminStats && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-bg-card border border-border-subtle rounded-xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <Users className="w-5 h-5 text-accent" />
                  <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                    Total Users
                  </span>
                </div>
                <span className="text-3xl font-bold text-text-main">
                  {adminStats.total_users}
                </span>
              </div>
              <div className="bg-bg-card border border-border-subtle rounded-xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <BarChart3 className="w-5 h-5 text-pass" />
                  <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                    Total Audits
                  </span>
                </div>
                <span className="text-3xl font-bold text-text-main">
                  {adminStats.total_audits}
                </span>
              </div>
              <div className="bg-bg-card border border-border-subtle rounded-xl p-6">
                <div className="flex items-center gap-3 mb-3">
                  <FileUp className="w-5 h-5 text-warn" />
                  <span className="text-xs font-bold text-text-muted uppercase tracking-wider">
                    Bulk Jobs
                  </span>
                </div>
                <span className="text-3xl font-bold text-text-main">
                  {adminStats.total_bulk_jobs}
                </span>
              </div>
            </div>
          )}

          {/* Create User */}
          <div className="bg-bg-card border border-border-subtle rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-accent" /> Create New User
            </h3>
            <form onSubmit={handleAdminCreate} className="flex gap-3">
              <input
                type="email"
                placeholder="New User Email"
                value={adminEmail}
                onChange={(e) => setAdminEmail(e.target.value)}
                className="flex-1 bg-bg-main border border-border-subtle p-3 rounded-lg outline-none focus:border-border-focus"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={adminPass}
                onChange={(e) => setAdminPass(e.target.value)}
                className="flex-1 bg-bg-main border border-border-subtle p-3 rounded-lg outline-none focus:border-border-focus"
                required
              />
              <button className="bg-accent text-accent-fg px-6 py-3 rounded-lg font-medium whitespace-nowrap">
                Create
              </button>
            </form>
            {adminStatus && (
              <p className="text-xs text-accent mt-3">{adminStatus}</p>
            )}
          </div>

          {/* Users Table */}
          <div className="bg-bg-card border border-border-subtle rounded-xl overflow-hidden">
            <div className="p-6 border-b border-border-subtle">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Users className="w-5 h-5 text-text-muted" /> Registered Users
              </h3>
            </div>
            {adminUsers.length === 0 ? (
              <div className="p-8 text-center text-text-muted text-sm">
                No users found.
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border-subtle text-left">
                    <th className="px-6 py-3 text-xs font-bold text-text-muted uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-xs font-bold text-text-muted uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-xs font-bold text-text-muted uppercase tracking-wider">
                      Audits
                    </th>
                    <th className="px-6 py-3 text-xs font-bold text-text-muted uppercase tracking-wider text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {adminUsers.map((u: any) => (
                    <tr
                      key={u.id}
                      className="border-b border-border-subtle last:border-0 hover:bg-bg-hover transition-colors"
                    >
                      <td className="px-6 py-4 text-sm text-text-muted">
                        #{u.id}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-text-main">
                        {u.email}
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1 text-sm font-bold text-accent">
                          <BarChart3 className="w-3.5 h-3.5" /> {u.audit_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleDeleteUser(u.id)}
                          className="p-2 text-text-muted hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                          title="Delete user"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}

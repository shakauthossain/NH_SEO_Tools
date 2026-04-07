import React, { useState } from "react";
import { motion } from "framer-motion";
import { Lock, Loader2 } from "lucide-react";
import api, { setAuthToken } from "../api";

interface AuthModalProps {
  isOpen: boolean;
  onSuccess: () => void;
}

export default function AuthModal({ isOpen, onSuccess }: AuthModalProps) {
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

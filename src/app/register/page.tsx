/* ================================================================
   Ev2Ev — Register Page
   Premium auth page for account creation with email + password
   ================================================================ */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/components/providers/AuthProvider";
import { Zap, Mail, Lock, User, ArrowRight, Eye, EyeOff, AlertCircle, MailCheck } from "lucide-react";

export default function RegisterPage() {
  const { t } = useI18n();
  const { signUp } = useAuth();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleRegister = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    const { error: authError } = await signUp(email, password, displayName);
    setSubmitting(false);
    if (authError) {
      setError(authError);
      return;
    }
    setSuccess(true);
  };

  return (
    <div className="min-h-screen gradient-hero flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-ev-green-500/10 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-navy-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: "1.5s" }} />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 group">
            <div className="w-12 h-12 rounded-2xl gradient-accent flex items-center justify-center shadow-glow group-hover:shadow-glow-lg transition-shadow">
              <Zap className="w-7 h-7 text-white" fill="currentColor" />
            </div>
            <span className="text-3xl font-bold gradient-text">Ev2Ev</span>
          </Link>
          <p className="text-gray-400 mt-2">{t("site.tagline")}</p>
        </div>

        {/* Auth Card */}
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
          {success ? (
            <div className="text-center" id="register-success">
              <div className="w-14 h-14 rounded-2xl bg-ev-green-500/10 border border-ev-green-500/30 flex items-center justify-center mx-auto mb-4">
                <MailCheck className="w-7 h-7 text-ev-green-400" />
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">Check your email</h1>
              <p className="text-sm text-gray-400 leading-relaxed">
                Check your email to confirm your account. We sent a confirmation link to{" "}
                <span className="text-white font-medium">{email}</span>.
              </p>
              <Link
                href="/login"
                className="mt-6 w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.01]"
                id="register-goto-login"
              >
                {t("auth.login")} <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-white text-center mb-6">{t("auth.register")}</h1>

              {/* Error Banner */}
              {error && (
                <div
                  className="flex items-start gap-2 px-4 py-3 mb-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
                  role="alert"
                  id="register-error"
                >
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1.5">Display Name</label>
                  <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-ev-green-500/50 transition-colors">
                    <User className="w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      placeholder="Your name"
                      className="w-full bg-transparent text-white placeholder:text-gray-600 text-sm focus:outline-none"
                      id="register-name"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1.5">{t("auth.email")}</label>
                  <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-ev-green-500/50 transition-colors">
                    <Mail className="w-4 h-4 text-gray-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="your@email.com"
                      className="w-full bg-transparent text-white placeholder:text-gray-600 text-sm focus:outline-none"
                      id="register-email"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1.5">{t("auth.password")}</label>
                  <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-ev-green-500/50 transition-colors">
                    <Lock className="w-4 h-4 text-gray-500" />
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full bg-transparent text-white placeholder:text-gray-600 text-sm focus:outline-none"
                      id="register-password"
                      minLength={6}
                      required
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="text-gray-500 hover:text-gray-300">
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.01] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
                  id="register-submit"
                >
                  {submitting ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Please wait…
                    </>
                  ) : (
                    <>
                      {t("auth.register")} <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Terms */}
              <p className="text-xs text-gray-500 text-center mt-6 leading-relaxed">
                {t("auth.terms")}
              </p>
            </>
          )}
        </div>

        {/* Login Link */}
        <p className="text-center text-sm text-gray-400 mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-ev-green-400 font-semibold hover:underline">
            {t("auth.login")}
          </Link>
        </p>
      </div>
    </div>
  );
}

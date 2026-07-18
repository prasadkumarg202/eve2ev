/* ================================================================
   Ev2Ev — Forgot Password Page
   Premium auth page for requesting a password reset email
   ================================================================ */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/components/providers/AuthProvider";
import { Zap, Mail, ArrowRight, ArrowLeft, AlertCircle, MailCheck } from "lucide-react";

export default function ForgotPasswordPage() {
  const { t } = useI18n();
  const { resetPassword } = useAuth();

  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleReset = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    const { error: authError } = await resetPassword(email);
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
            <div className="text-center" id="forgot-success">
              <div className="w-14 h-14 rounded-2xl bg-ev-green-500/10 border border-ev-green-500/30 flex items-center justify-center mx-auto mb-4">
                <MailCheck className="w-7 h-7 text-ev-green-400" />
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">Check your email</h1>
              <p className="text-sm text-gray-400 leading-relaxed">
                If an account exists, a reset link has been sent to your email.
              </p>
              <Link
                href="/login"
                className="mt-6 w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.01]"
                id="forgot-goto-login"
              >
                {t("auth.login")} <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-white text-center mb-2">Reset Password</h1>
              <p className="text-sm text-gray-400 text-center mb-6">
                Enter your email and we&apos;ll send you a link to reset your password.
              </p>

              {/* Error Banner */}
              {error && (
                <div
                  className="flex items-start gap-2 px-4 py-3 mb-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
                  role="alert"
                  id="forgot-error"
                >
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleReset} className="space-y-4">
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
                      id="forgot-email"
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.01] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
                  id="forgot-submit"
                >
                  {submitting ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Please wait…
                    </>
                  ) : (
                    <>
                      Send Reset Link <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          )}
        </div>

        {/* Back to Login */}
        <p className="text-center text-sm text-gray-400 mt-6">
          <Link href="/login" className="inline-flex items-center gap-1 text-ev-green-400 font-semibold hover:underline">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to {t("auth.login")}
          </Link>
        </p>
      </div>
    </div>
  );
}

/* ================================================================
   Ev2Ev — Login Page
   Premium auth page with email, Google, and phone OTP options
   ================================================================ */

"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/components/providers/AuthProvider";
import { Zap, Mail, Lock, Phone, ArrowRight, Eye, EyeOff, AlertCircle } from "lucide-react";

type AuthTab = "email" | "phone";

function LoginPageContent() {
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signInWithPassword, signInWithOtp, verifyOtp, signInWithGoogle } = useAuth();

  const [tab, setTab] = useState<AuthTab>("email");
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const callbackError = searchParams.get("error");

  const handleEmailLogin = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    const { error: authError } = await signInWithPassword(email, password);
    if (authError) {
      setError(authError);
      setSubmitting(false);
      return;
    }
    router.push("/");
    router.refresh();
  };

  const handleSendOtp = async () => {
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    const { error: authError } = await signInWithOtp(phone);
    setSubmitting(false);
    if (authError) {
      setError(authError);
      return;
    }
    setOtpSent(true);
  };

  const handleVerifyOtp = async () => {
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    const { error: authError } = await verifyOtp(phone, otp);
    if (authError) {
      setError(authError);
      setSubmitting(false);
      return;
    }
    router.push("/");
    router.refresh();
  };

  const handleGoogleLogin = async () => {
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    const { error: authError } = await signInWithGoogle();
    if (authError) {
      setError(authError);
      setSubmitting(false);
    }
    // On success the browser is redirected to Google — keep the button disabled.
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
          <h1 className="text-2xl font-bold text-white text-center mb-6">{t("auth.login")}</h1>

          {/* Error Banner */}
          {(error || callbackError) && (
            <div
              className="flex items-start gap-2 px-4 py-3 mb-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
              role="alert"
              id="login-error"
            >
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error || callbackError}</span>
            </div>
          )}

          {/* Tab Selector */}
          <div className="flex rounded-xl bg-white/5 p-1 mb-6">
            <button
              onClick={() => setTab("email")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                tab === "email"
                  ? "bg-white/10 text-white shadow"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <Mail className="w-4 h-4" /> {t("auth.email")}
            </button>
            <button
              onClick={() => setTab("phone")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                tab === "phone"
                  ? "bg-white/10 text-white shadow"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <Phone className="w-4 h-4" /> {t("auth.phone")}
            </button>
          </div>

          {/* Email Form */}
          {tab === "email" && (
            <form onSubmit={handleEmailLogin} className="space-y-4">
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
                    id="login-email"
                    required
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm text-gray-400">{t("auth.password")}</label>
                  <Link href="/forgot-password" className="text-xs text-ev-green-400 hover:underline">
                    {t("auth.forgotPassword")}
                  </Link>
                </div>
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-ev-green-500/50 transition-colors">
                  <Lock className="w-4 h-4 text-gray-500" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-transparent text-white placeholder:text-gray-600 text-sm focus:outline-none"
                    id="login-password"
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
                id="login-submit"
              >
                {submitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Please wait…
                  </>
                ) : (
                  <>
                    {t("auth.login")} <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Phone OTP Form */}
          {tab === "phone" && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">{t("auth.phone")}</label>
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-ev-green-500/50 transition-colors">
                  <span className="text-gray-500 text-sm">+91</span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="98765 43210"
                    className="w-full bg-transparent text-white placeholder:text-gray-600 text-sm focus:outline-none"
                    id="login-phone"
                    maxLength={10}
                  />
                </div>
              </div>

              {otpSent && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1.5">{t("auth.otp")}</label>
                  <div className="flex gap-2">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <input
                        key={i}
                        type="text"
                        maxLength={1}
                        value={otp[i] || ""}
                        onChange={(e) => {
                          const newOtp = otp.split("");
                          newOtp[i] = e.target.value;
                          setOtp(newOtp.join(""));
                          if (e.target.value && e.target.nextElementSibling) {
                            (e.target.nextElementSibling as HTMLInputElement).focus();
                          }
                        }}
                        className="w-full aspect-square rounded-xl bg-white/5 border border-white/10 text-white text-center text-lg font-bold focus:outline-none focus:border-ev-green-500/50"
                        id={`otp-input-${i}`}
                      />
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={otpSent ? handleVerifyOtp : handleSendOtp}
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.01] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
                id="otp-submit"
              >
                {submitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Please wait…
                  </>
                ) : (
                  <>
                    {otpSent ? t("auth.verifyOtp") : t("auth.sendOtp")} <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          )}

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-gray-500">{t("auth.orContinueWith")}</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          {/* Social Login */}
          <button
            onClick={handleGoogleLogin}
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-white/10 text-white font-medium hover:bg-white/5 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            id="google-login"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            {t("auth.google")}
          </button>

          {/* Terms */}
          <p className="text-xs text-gray-500 text-center mt-6 leading-relaxed">
            {t("auth.terms")}
          </p>
        </div>

        {/* Register Link */}
        <p className="text-center text-sm text-gray-400 mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-ev-green-400 font-semibold hover:underline">
            {t("auth.register")}
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen gradient-hero flex items-center justify-center">
          <div className="w-10 h-10 border-3 border-ev-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  );
}

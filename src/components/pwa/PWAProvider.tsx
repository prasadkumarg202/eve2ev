/* ================================================================
   Ev2Ev — PWA Provider (client)
   Registers the service worker and renders an unobtrusive
   "Add to Home Screen" install prompt (Android/Chromium via
   beforeinstallprompt, iOS via manual instructions).
   ================================================================ */

"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, X, Share, Plus, Zap } from "lucide-react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISS_KEY = "ev2ev-install-dismissed";

export default function PWAProvider() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [visible, setVisible] = useState(false);

  // Register the service worker once, after load.
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;
    if (process.env.NODE_ENV !== "production") return; // avoid dev caching headaches

    const onLoad = () => {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/", updateViaCache: "none" })
        .catch(() => {
          /* registration failures shouldn't break the app */
        });
    };
    window.addEventListener("load", onLoad);
    return () => window.removeEventListener("load", onLoad);
  }, []);

  // Decide whether to show the install affordance.
  useEffect(() => {
    if (typeof window === "undefined") return;

    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      // iOS Safari
      (window.navigator as unknown as { standalone?: boolean }).standalone === true;
    if (standalone) return; // already installed

    if (localStorage.getItem(DISMISS_KEY)) return; // user said no recently

    const ios =
      /iphone|ipad|ipod/i.test(window.navigator.userAgent) &&
      !(window as unknown as { MSStream?: unknown }).MSStream;
    setIsIOS(ios);

    const onBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
      setVisible(true);
    };
    window.addEventListener("beforeinstallprompt", onBeforeInstall);

    // iOS never fires beforeinstallprompt — show the manual hint after a beat.
    let iosTimer: ReturnType<typeof setTimeout> | undefined;
    if (ios) iosTimer = setTimeout(() => setVisible(true), 2500);

    const onInstalled = () => {
      setVisible(false);
      setDeferred(null);
    };
    window.addEventListener("appinstalled", onInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstall);
      window.removeEventListener("appinstalled", onInstalled);
      if (iosTimer) clearTimeout(iosTimer);
    };
  }, []);

  const dismiss = useCallback(() => {
    setVisible(false);
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      /* ignore */
    }
  }, []);

  const install = useCallback(async () => {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
    setVisible(false);
  }, [deferred]);

  if (!visible) return null;

  return (
    <div
      className="fixed inset-x-0 z-[60] px-3 pointer-events-none"
      style={{ bottom: "calc(var(--bottom-nav-h, 0px) + env(safe-area-inset-bottom) + 0.75rem)" }}
    >
      <div className="pointer-events-auto max-w-md mx-auto rounded-2xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-2xl p-4 flex items-start gap-3 animate-slide-up">
        <div className="w-10 h-10 rounded-xl gradient-accent text-white flex items-center justify-center shrink-0 shadow-glow">
          <Zap className="w-5 h-5" fill="currentColor" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[var(--text-primary)]">Install Ev2Ev</p>
          {isIOS ? (
            <p className="text-xs text-[var(--text-secondary)] mt-0.5 leading-relaxed">
              Tap <Share className="inline w-3.5 h-3.5 -mt-0.5" /> then{" "}
              <span className="font-medium">Add to Home Screen</span>{" "}
              <Plus className="inline w-3.5 h-3.5 -mt-0.5" /> for the full app.
            </p>
          ) : (
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              Add it to your home screen for offline maps and faster access.
            </p>
          )}
          {!isIOS && (
            <button
              onClick={install}
              className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold gradient-accent text-white shadow-glow"
              id="pwa-install-btn"
            >
              <Download className="w-3.5 h-3.5" /> Install
            </button>
          )}
        </div>
        <button
          onClick={dismiss}
          className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] shrink-0"
          aria-label="Dismiss install prompt"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/* ================================================================
   Ev2Ev — Offline Fallback
   Served by the service worker when a navigation fails with no
   cached copy available.
   ================================================================ */

import Link from "next/link";
import { WifiOff, RefreshCw, Search } from "lucide-react";

export const metadata = {
  title: "You're offline",
};

export default function OfflinePage() {
  return (
    <div className="min-h-screen gradient-hero flex items-center justify-center p-6 text-center">
      <div className="max-w-sm">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-white/10 border border-white/10 flex items-center justify-center mb-6">
          <WifiOff className="w-8 h-8 text-ev-green-400" />
        </div>
        <h1 className="text-2xl font-bold text-white">You&apos;re offline</h1>
        <p className="text-gray-400 mt-2">
          We couldn&apos;t reach the network. Pages you&apos;ve already visited
          are still available, and Ev2Ev will reconnect automatically.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold gradient-accent text-white shadow-glow"
          >
            <RefreshCw className="w-4 h-4" /> Try Home
          </Link>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white border border-white/20 hover:bg-white/10 transition-colors"
          >
            <Search className="w-4 h-4" /> Cached Chargers
          </Link>
        </div>
      </div>
    </div>
  );
}

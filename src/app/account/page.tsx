/* ================================================================
   Ev2Ev — Account Page
   Shows the signed-in user's profile and sign-out. Redirects to
   /login when unauthenticated.
   ================================================================ */

"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { User, Mail, Phone, LogOut, Heart, Star, Zap } from "lucide-react";

export default function AccountPage() {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login?next=/account");
    }
  }, [loading, user, router]);

  const handleSignOut = async () => {
    await signOut();
    router.replace("/");
    router.refresh();
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="w-10 h-10 border-3 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
        </div>
        <Footer />
      </div>
    );
  }

  const displayName =
    (user.user_metadata?.full_name as string | undefined) ||
    user.email?.split("@")[0] ||
    "EV Driver";
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-10">
        {/* Profile header */}
        <div className="card p-6 flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl gradient-accent text-white flex items-center justify-center text-2xl font-bold shadow-glow">
            {initial}
          </div>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-[var(--text-primary)] truncate">{displayName}</h1>
            <div className="mt-1 space-y-0.5">
              {user.email && (
                <p className="flex items-center gap-1.5 text-sm text-[var(--text-secondary)] truncate">
                  <Mail className="w-3.5 h-3.5" /> {user.email}
                </p>
              )}
              {user.phone && (
                <p className="flex items-center gap-1.5 text-sm text-[var(--text-secondary)]">
                  <Phone className="w-3.5 h-3.5" /> {user.phone}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
          <Link href="/search" className="card p-5 group">
            <Zap className="w-6 h-6 text-ev-green-400 mb-2" />
            <p className="font-semibold text-[var(--text-primary)]">Find Chargers</p>
            <p className="text-sm text-[var(--text-secondary)]">Search stations near you</p>
          </Link>
          <div className="card p-5">
            <Heart className="w-6 h-6 text-red-400 mb-2" />
            <p className="font-semibold text-[var(--text-primary)]">Favorites</p>
            <p className="text-sm text-[var(--text-secondary)]">Saved from station pages</p>
          </div>
          <div className="card p-5">
            <Star className="w-6 h-6 text-amber-400 mb-2" />
            <p className="font-semibold text-[var(--text-primary)]">My Reviews</p>
            <p className="text-sm text-[var(--text-secondary)]">Reviews you&apos;ve written</p>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <User className="w-4 h-4" /> Back to home
          </Link>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold text-red-500 border border-red-500/20 hover:bg-red-500/10 transition-colors"
            id="account-logout"
          >
            <LogOut className="w-4 h-4" /> Log Out
          </button>
        </div>
      </main>

      <Footer />
    </div>
  );
}

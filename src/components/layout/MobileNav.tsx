/* ================================================================
   Ev2Ev — Mobile Bottom Navigation
   App-style tab bar shown only on small screens. Respects the
   device safe-area inset. Hidden on md+ where the Header nav shows.
   ================================================================ */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/components/providers/AuthProvider";
import { Home, Search, Route, User, LogIn } from "lucide-react";
import type { ComponentType } from "react";

interface Tab {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  match: (path: string) => boolean;
}

export default function MobileNav() {
  const pathname = usePathname();
  const { t } = useI18n();
  const { user } = useAuth();

  // Hide the tab bar on immersive/auth screens.
  if (
    pathname === "/login" ||
    pathname === "/register" ||
    pathname === "/forgot-password" ||
    pathname === "/offline"
  ) {
    return null;
  }

  const tabs: Tab[] = [
    { href: "/", label: t("nav.home"), icon: Home, match: (p) => p === "/" },
    { href: "/search", label: t("nav.search"), icon: Search, match: (p) => p.startsWith("/search") || p.startsWith("/station") },
    { href: "/route-planner", label: t("nav.routePlanner"), icon: Route, match: (p) => p.startsWith("/route-planner") },
    user
      ? { href: "/account", label: t("nav.profile"), icon: User, match: (p) => p.startsWith("/account") }
      : { href: "/login", label: t("nav.login"), icon: LogIn, match: (p) => p.startsWith("/login") },
  ];

  return (
    <nav
      className="md:hidden fixed bottom-0 inset-x-0 z-50 glass-heavy border-t border-[var(--border-primary)]"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      id="mobile-bottom-nav"
      aria-label="Primary"
    >
      <div className="grid grid-cols-4 h-16">
        {tabs.map((tab) => {
          const active = tab.match(pathname);
          const Icon = tab.icon;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition-colors ${
                active
                  ? "text-[var(--accent)]"
                  : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon className={`w-5 h-5 ${active ? "scale-110" : ""} transition-transform`} />
              <span className="truncate max-w-full px-1">{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

/* ================================================================
   Ev2Ev — Header Component
   Responsive navigation with glassmorphism, theme toggle, language switcher
   ================================================================ */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { useTheme } from "@/components/providers/ThemeProvider";
import { useAuth } from "@/components/providers/AuthProvider";
import { useAppStore } from "@/lib/store";
import {
  Zap, Search, MapPin, Route, BookOpen, Menu, X,
  Sun, Moon, Globe, User, LogIn, LogOut, ChevronDown
} from "lucide-react";
import { LANGUAGES } from "@/lib/utils/constants";

export default function Header() {
  const { t, locale, setLocale } = useI18n();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { user, signOut } = useAuth();
  const { isMobileMenuOpen, setMobileMenuOpen } = useAppStore();
  const router = useRouter();
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  const userLabel =
    (user?.user_metadata?.full_name as string | undefined) ||
    user?.email ||
    user?.phone ||
    "Account";
  const userInitial = userLabel.charAt(0).toUpperCase();

  const handleSignOut = async () => {
    setShowUserDropdown(false);
    await signOut();
    router.refresh();
  };

  const navLinks = [
    { href: "/", label: t("nav.home"), icon: <Zap className="w-4 h-4" /> },
    { href: "/search", label: t("nav.search"), icon: <Search className="w-4 h-4" /> },
    { href: "/route-planner", label: t("nav.routePlanner"), icon: <Route className="w-4 h-4" /> },
    { href: "/blog", label: t("nav.blog"), icon: <BookOpen className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 glass-heavy">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group" id="header-logo">
            <div className="w-9 h-9 rounded-xl gradient-accent flex items-center justify-center shadow-glow group-hover:shadow-glow-lg transition-shadow">
              <Zap className="w-5 h-5 text-white" fill="currentColor" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              <span className="gradient-text">Ev2Ev</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1" id="desktop-nav">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                {link.icon}
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {/* Language Switcher */}
            <div className="relative hidden sm:block">
              <button
                onClick={() => setShowLangDropdown(!showLangDropdown)}
                className="flex items-center gap-1 px-2.5 py-2 rounded-lg text-sm transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
                id="language-switcher"
                aria-label={t("nav.language")}
              >
                <Globe className="w-4 h-4" />
                <span className="uppercase text-xs font-semibold">{locale}</span>
                <ChevronDown className="w-3 h-3" />
              </button>
              {showLangDropdown && (
                <div className="absolute right-0 mt-1 w-48 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-xl animate-scale-in overflow-hidden">
                  {LANGUAGES.slice(0, 2).map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setLocale(lang.code as "en" | "hi");
                        setShowLangDropdown(false);
                      }}
                      className={`w-full text-left px-4 py-2.5 text-sm transition-colors hover:bg-[var(--bg-secondary)] ${
                        locale === lang.code
                          ? "text-[var(--accent)] font-semibold"
                          : "text-[var(--text-primary)]"
                      }`}
                    >
                      {lang.nativeName} ({lang.name})
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
              id="theme-toggle"
              aria-label="Toggle theme"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>

            {/* Auth: User Menu or Login Button */}
            {user ? (
              <div className="relative hidden sm:block">
                <button
                  onClick={() => setShowUserDropdown(!showUserDropdown)}
                  className="flex items-center gap-2 pl-1.5 pr-2.5 py-1.5 rounded-xl text-sm font-medium transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border-primary)]"
                  id="user-menu-button"
                  aria-label="Account menu"
                >
                  <span className="w-7 h-7 rounded-full gradient-accent text-white flex items-center justify-center text-xs font-bold">
                    {userInitial}
                  </span>
                  <span className="max-w-[120px] truncate">{userLabel}</span>
                  <ChevronDown className="w-3 h-3" />
                </button>
                {showUserDropdown && (
                  <div className="absolute right-0 mt-1 w-56 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-xl animate-scale-in overflow-hidden">
                    <div className="px-4 py-3 border-b border-[var(--border-primary)]">
                      <p className="text-sm font-semibold text-[var(--text-primary)] truncate">{userLabel}</p>
                      {user.email && (
                        <p className="text-xs text-[var(--text-tertiary)] truncate">{user.email}</p>
                      )}
                    </div>
                    <Link
                      href="/account"
                      onClick={() => setShowUserDropdown(false)}
                      className="flex items-center gap-2 px-4 py-2.5 text-sm text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-secondary)]"
                    >
                      <User className="w-4 h-4" /> My Account
                    </Link>
                    <button
                      onClick={handleSignOut}
                      className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-500 transition-colors hover:bg-[var(--bg-secondary)]"
                      id="logout-button"
                    >
                      <LogOut className="w-4 h-4" /> {t("nav.logout")}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                href="/login"
                className="hidden sm:flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.02]"
                id="login-button"
              >
                <LogIn className="w-4 h-4" />
                {t("nav.login")}
              </Link>
            )}

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-lg transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
              id="mobile-menu-toggle"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-[var(--border-primary)] animate-slide-down">
          <div className="px-4 py-3 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
              >
                {link.icon}
                {link.label}
              </Link>
            ))}
            <div className="pt-2 border-t border-[var(--border-primary)] space-y-1">
              {user ? (
                <>
                  <Link
                    href="/account"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
                  >
                    <User className="w-4 h-4" /> {userLabel}
                  </Link>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      handleSignOut();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold text-red-500 hover:bg-[var(--bg-tertiary)]"
                  >
                    <LogOut className="w-4 h-4" /> {t("nav.logout")}
                  </button>
                </>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold gradient-accent text-white"
                >
                  <LogIn className="w-4 h-4" />
                  {t("nav.login")}
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

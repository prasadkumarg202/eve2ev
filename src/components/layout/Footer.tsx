/* ================================================================
   Ev2Ev — Footer Component
   Comprehensive footer with links, social, and branding
   ================================================================ */

"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { Zap, MapPin, Mail, Phone, MessageCircle, GitBranch, Link2, Heart } from "lucide-react";

export default function Footer() {
  const { t } = useI18n();

  return (
    <footer className="border-t border-[var(--border-primary)] bg-[var(--bg-secondary)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl gradient-accent flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" fill="currentColor" />
              </div>
              <span className="text-xl font-bold gradient-text">Ev2Ev</span>
            </Link>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {t("footer.aboutDesc")}
            </p>
            <div className="flex gap-3">
              <a href="#" className="p-2 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors" aria-label="Twitter">
                <MessageCircle className="w-4 h-4" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors" aria-label="GitHub">
                <GitBranch className="w-4 h-4" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors" aria-label="LinkedIn">
                <Link2 className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-sm uppercase tracking-wider text-[var(--text-primary)] mb-4">
              {t("footer.quickLinks")}
            </h3>
            <ul className="space-y-2.5">
              {[
                { href: "/search", label: "Find Chargers" },
                { href: "/route-planner", label: "Route Planner" },
                { href: "/blog", label: "Travel Blog" },
                { href: "/community/leaderboard", label: "Leaderboard" },
                { href: "/explore/delhi", label: "Delhi Chargers" },
                { href: "/explore/mumbai", label: "Mumbai Chargers" },
                { href: "/explore/bangalore", label: "Bangalore Chargers" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="font-semibold text-sm uppercase tracking-wider text-[var(--text-primary)] mb-4">
              {t("footer.support")}
            </h3>
            <ul className="space-y-2.5">
              {[
                { href: "/faq", label: t("footer.faq") },
                { href: "/contact", label: t("footer.contact") },
                { href: "/privacy", label: t("footer.privacy") },
                { href: "/terms", label: t("footer.terms") },
                { href: "/operators", label: t("footer.operators") },
                { href: "/developers", label: t("footer.developers") },
                { href: "/careers", label: t("footer.careers") },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="font-semibold text-sm uppercase tracking-wider text-[var(--text-primary)] mb-4">
              {t("footer.contact")}
            </h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-2 text-sm text-[var(--text-secondary)]">
                <MapPin className="w-4 h-4 mt-0.5 text-[var(--accent)] shrink-0" />
                <span>Hyderabad, Telangana, India</span>
              </li>
              <li className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Mail className="w-4 h-4 text-[var(--accent)] shrink-0" />
                <a href="mailto:hello@ev2ev.in" className="hover:text-[var(--accent)] transition-colors">
                  hello@ev2ev.in
                </a>
              </li>
              <li className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <Phone className="w-4 h-4 text-[var(--accent)] shrink-0" />
                <a href="tel:+911800000000" className="hover:text-[var(--accent)] transition-colors">
                  1800-EV2-EV2E
                </a>
              </li>
            </ul>

            {/* Newsletter */}
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Stay Updated</h4>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="Your email"
                  className="flex-1 px-3 py-2 rounded-lg text-sm bg-[var(--bg-primary)] border border-[var(--border-primary)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]"
                  id="footer-newsletter-input"
                />
                <button className="px-3 py-2 rounded-lg text-sm font-semibold gradient-accent text-white hover:shadow-glow transition-shadow">
                  Join
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-6 border-t border-[var(--border-primary)] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-[var(--text-tertiary)]">
            {t("footer.copyright")}
          </p>
          <p className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
            Made with <Heart className="w-3 h-3 text-red-500" fill="currentColor" /> & <Zap className="w-3 h-3 text-[var(--accent)]" fill="currentColor" /> in India
          </p>
        </div>
      </div>
    </footer>
  );
}

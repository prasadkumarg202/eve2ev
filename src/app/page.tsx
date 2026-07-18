/* ================================================================
   Ev2Ev — Home Page
   Hero section, search, map discovery, stats, featured stations
   ================================================================ */

"use client";

import { useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { useStations, useStationStats } from "@/hooks/useStations";
import { useAppStore } from "@/lib/store";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import StationCard from "@/components/station/StationCard";
import {
  Search, MapPin, Zap, Star, Building2, Users, ChevronRight,
  Route, Brain, Shield, Smartphone, BatteryCharging, Globe,
  ArrowRight, Sparkles, TrendingUp
} from "lucide-react";
import { OPERATORS_LIST, CONNECTOR_TYPES, VEHICLE_TYPES } from "@/lib/utils/constants";

// Dynamic import for MapView (no SSR)
const MapView = dynamic(() => import("@/components/map/MapView"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-[var(--bg-secondary)] rounded-xl flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-3 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-[var(--text-secondary)]">Loading map...</p>
      </div>
    </div>
  ),
});

export default function HomePage() {
  const { t } = useI18n();
  const stats = useStationStats();
  const [searchQuery, setSearchQuery] = useState("");
  const { setSelectedStation } = useAppStore();

  const { stations: featuredStations } = useStations({
    sortBy: "rating",
    limit: 6,
  });

  const { allStations } = useStations();

  const handleSearch = useCallback(() => {
    if (searchQuery.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`;
    }
  }, [searchQuery]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleSearch();
    },
    [handleSearch]
  );

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      {/* ============ HERO SECTION ============ */}
      <section className="gradient-hero relative overflow-hidden" id="hero-section">
        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-10 w-72 h-72 bg-ev-green-500/10 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-navy-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: "1.5s" }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-ev-green-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 pt-16 pb-20 md:pt-24 md:pb-28">
          {/* Badge */}
          <div className="flex justify-center mb-6 animate-fade-in">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-ev-green-500/15 text-ev-green-400 border border-ev-green-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              India&apos;s First Unified EV Charging Platform
            </span>
          </div>

          {/* Heading */}
          <h1 className="text-center text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-white leading-[1.1] tracking-tight max-w-4xl mx-auto animate-slide-up">
            {t("home.heroTitle").split(" ").map((word, i) => (
              <span key={i}>
                {word === "Every" || word === "हर" ? (
                  <span className="gradient-text">{word}</span>
                ) : (
                  word
                )}{" "}
              </span>
            ))}
          </h1>

          {/* Subtitle */}
          <p className="text-center text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mt-6 animate-slide-up" style={{ animationDelay: "0.1s" }}>
            {t("home.heroSubtitle")}
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mt-10 animate-slide-up" style={{ animationDelay: "0.2s" }}>
            <div className="flex items-center gap-2 p-2 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/10 shadow-2xl focus-within:border-ev-green-500/50 transition-colors">
              <div className="flex items-center gap-2 flex-1 px-4">
                <Search className="w-5 h-5 text-gray-400 shrink-0" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t("home.searchPlaceholder")}
                  className="w-full bg-transparent text-white placeholder:text-gray-500 text-base md:text-lg py-3 focus:outline-none"
                  id="hero-search-input"
                />
              </div>
              <button
                onClick={() => {
                  navigator.geolocation?.getCurrentPosition((pos) => {
                    window.location.href = `/search?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`;
                  });
                }}
                className="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm text-gray-400 hover:text-ev-green-400 hover:bg-white/5 transition-colors"
                id="use-location-btn"
              >
                <MapPin className="w-4 h-4" />
                <span className="hidden md:inline">{t("home.useLocation")}</span>
              </button>
              <button
                onClick={handleSearch}
                className="px-6 py-3 rounded-xl text-sm md:text-base font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.02] shrink-0"
                id="hero-search-btn"
              >
                {t("home.searchButton")}
              </button>
            </div>

            {/* Quick Search Tags */}
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", "NH-44"].map((tag) => (
                <Link
                  key={tag}
                  href={`/search?q=${encodeURIComponent(tag)}`}
                  className="px-3 py-1 rounded-full text-xs font-medium text-gray-400 border border-white/10 hover:border-ev-green-500/30 hover:text-ev-green-400 hover:bg-ev-green-500/5 transition-all"
                >
                  {tag}
                </Link>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 max-w-3xl mx-auto mt-16 animate-slide-up" style={{ animationDelay: "0.3s" }}>
            {[
              { value: `${stats.stationCount}+`, label: t("home.stats.stations"), icon: <Zap className="w-5 h-5" /> },
              { value: `${stats.cityCount}+`, label: t("home.stats.cities"), icon: <Building2 className="w-5 h-5" /> },
              { value: `${stats.operatorCount}+`, label: t("home.stats.operators"), icon: <Globe className="w-5 h-5" /> },
              { value: `${(stats.reviewCount / 1000).toFixed(1)}K+`, label: t("home.stats.reviews"), icon: <Star className="w-5 h-5" /> },
            ].map((stat) => (
              <div key={stat.label} className="text-center group">
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-ev-green-500/10 text-ev-green-400 mb-2 group-hover:bg-ev-green-500/20 transition-colors">
                  {stat.icon}
                </div>
                <div className="text-2xl md:text-3xl font-extrabold text-white">{stat.value}</div>
                <div className="text-xs md:text-sm text-gray-500 mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ MAP SECTION ============ */}
      <section className="py-12 md:py-16 bg-[var(--bg-primary)]" id="map-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">
                Explore Chargers on Map
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Interactive map with all charging stations across India
              </p>
            </div>
            <Link
              href="/search"
              className="hidden sm:flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
            >
              {t("home.viewAll")} <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="h-[500px] md:h-[600px] rounded-2xl overflow-hidden border border-[var(--border-primary)] shadow-xl">
            <MapView
              stations={allStations}
              onStationClick={(station) => setSelectedStation(station)}
            />
          </div>
        </div>
      </section>

      {/* ============ FEATURED STATIONS ============ */}
      <section className="py-12 md:py-16 bg-[var(--bg-secondary)]" id="featured-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">
                {t("home.featured")}
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Top-rated charging stations across India
              </p>
            </div>
            <Link
              href="/search?sortBy=rating"
              className="flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
            >
              {t("home.viewAll")} <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredStations.map((station) => (
              <StationCard key={station.id} station={station} />
            ))}
          </div>
        </div>
      </section>

      {/* ============ OPERATORS SHOWCASE ============ */}
      <section className="py-12 md:py-16 bg-[var(--bg-primary)]" id="operators-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">
            {t("home.operators")}
          </h2>
          <p className="text-[var(--text-secondary)] mt-2 max-w-xl mx-auto">
            {t("home.operatorsDesc")}
          </p>

          <div className="flex flex-wrap justify-center gap-3 mt-8">
            {OPERATORS_LIST.slice(0, 15).map((op) => (
              <div
                key={op}
                className="px-4 py-2.5 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-sm font-medium text-[var(--text-secondary)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-all cursor-default"
              >
                {op}
              </div>
            ))}
            <div className="px-4 py-2.5 rounded-xl border border-dashed border-[var(--border-secondary)] text-sm font-medium text-[var(--text-tertiary)]">
              +{OPERATORS_LIST.length - 15} more
            </div>
          </div>
        </div>
      </section>

      {/* ============ FEATURES GRID ============ */}
      <section className="py-12 md:py-20 bg-[var(--bg-secondary)]" id="features-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">
              Everything You Need for EV Travel
            </h2>
            <p className="text-[var(--text-secondary)] mt-2 max-w-xl mx-auto">
              More than just finding chargers — plan trips, read reviews, and join the community.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: <Search className="w-6 h-6" />,
                title: "Smart Search",
                desc: "Find chargers by city, highway, PIN code, or nearby landmarks. Filter by connector, power, price, and more.",
                color: "text-ev-green-400",
                bg: "bg-ev-green-500/10",
              },
              {
                icon: <Route className="w-6 h-6" />,
                title: "Route Planner",
                desc: "Plan your EV trip with optimal charging stops. Enter battery % and vehicle type for precise calculations.",
                color: "text-navy-400",
                bg: "bg-navy-500/10",
              },
              {
                icon: <Brain className="w-6 h-6" />,
                title: "AI Assistant",
                desc: "Ask in natural language: 'Can I reach Tirupati with 35% battery?' or 'Find cheapest charger with restaurant'.",
                color: "text-amber-400",
                bg: "bg-amber-500/10",
              },
              {
                icon: <Star className="w-6 h-6" />,
                title: "Reviews & Ratings",
                desc: "Read real user reviews with waiting times, photos, and tips. Contribute your own experiences.",
                color: "text-amber-400",
                bg: "bg-amber-500/10",
              },
              {
                icon: <Smartphone className="w-6 h-6" />,
                title: "Book a Slot",
                desc: "Reserve your charging slot in advance. Get a QR code for seamless check-in at the station.",
                color: "text-ev-green-400",
                bg: "bg-ev-green-500/10",
              },
              {
                icon: <Shield className="w-6 h-6" />,
                title: "Community Verified",
                desc: "Crowd-sourced updates on charger availability, broken chargers, and new station discoveries.",
                color: "text-navy-400",
                bg: "bg-navy-500/10",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="card p-6 group"
              >
                <div className={`w-12 h-12 rounded-xl ${feature.bg} ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ CTA SECTION ============ */}
      <section className="py-12 md:py-20 gradient-hero relative overflow-hidden" id="cta-section">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 right-20 w-60 h-60 bg-ev-green-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-10 left-20 w-80 h-80 bg-navy-500/10 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t("home.cta.title")}
          </h2>
          <p className="text-lg text-gray-400 mb-8 max-w-xl mx-auto">
            {t("home.cta.description")}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/route-planner"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl text-base font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.02]"
              id="cta-route-planner"
            >
              <Route className="w-5 h-5" />
              {t("home.cta.button")}
            </Link>
            <Link
              href="/search"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl text-base font-semibold text-white border border-white/20 hover:bg-white/10 transition-all"
              id="cta-search"
            >
              <Search className="w-5 h-5" />
              Find Chargers
            </Link>
          </div>
        </div>
      </section>

      {/* ============ VEHICLE TYPES ============ */}
      <section className="py-12 md:py-16 bg-[var(--bg-primary)]" id="vehicles-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)] mb-2">
            For Every Electric Vehicle
          </h2>
          <p className="text-[var(--text-secondary)] mb-8">
            Whether you ride a bike, drive a car, or manage a fleet
          </p>

          <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            {VEHICLE_TYPES.map((vt) => (
              <Link
                key={vt.value}
                href={`/search?vehicle=${vt.value}`}
                className="card p-4 text-center group cursor-pointer"
              >
                <div className="text-3xl mb-2 group-hover:scale-125 transition-transform">
                  {vt.icon}
                </div>
                <div className="text-sm font-medium text-[var(--text-primary)]">{vt.label}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

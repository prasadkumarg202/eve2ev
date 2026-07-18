/* ================================================================
   Ev2Ev — Station Detail Page
   SEO-optimized page for each charging station
   ================================================================ */

"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useStation } from "@/hooks/useStations";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import ReviewsSection from "@/components/station/ReviewsSection";
import { createClient } from "@/lib/supabase/client";
import { isSupabaseConfigured } from "@/lib/supabase/env";
import { useAuth } from "@/components/providers/AuthProvider";
import {
  MapPin, Star, Zap, Clock, ParkingCircle, CheckCircle2,
  BatteryCharging, Phone, Mail, Globe, Navigation, Share2,
  Heart, AlertTriangle, Edit, ChevronRight, ArrowLeft,
  Coffee, UtensilsCrossed, Hotel, Hospital, Fuel,
  CreditCard, ShoppingBag, Landmark, Building2
} from "lucide-react";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

export default function StationDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const station = useStation(slug);
  const router = useRouter();
  const { user } = useAuth();

  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteBusy, setFavoriteBusy] = useState(false);

  // Load the initial favorite state for the logged-in user.
  useEffect(() => {
    if (!user || !isSupabaseConfigured()) {
      setIsFavorite(false);
      return;
    }
    let active = true;
    const supabase = createClient();
    supabase
      .from("favorites")
      .select("station_slug")
      .eq("user_id", user.id)
      .eq("station_slug", slug)
      .maybeSingle()
      .then(({ data }) => {
        if (active) setIsFavorite(Boolean(data));
      });
    return () => {
      active = false;
    };
  }, [user, slug]);

  const toggleFavorite = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    if (!isSupabaseConfigured() || favoriteBusy) return;

    setFavoriteBusy(true);
    const supabase = createClient();
    if (isFavorite) {
      const { error } = await supabase
        .from("favorites")
        .delete()
        .eq("user_id", user.id)
        .eq("station_slug", slug);
      if (!error) setIsFavorite(false);
    } else {
      const { error } = await supabase
        .from("favorites")
        .insert({ user_id: user.id, station_slug: slug });
      // 23505 = already favorited (e.g. from another tab) — treat as success.
      if (!error || error.code === "23505") setIsFavorite(true);
    }
    setFavoriteBusy(false);
  };

  if (!station) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Station Not Found</h1>
            <p className="text-[var(--text-secondary)] mt-2">The charging station you&apos;re looking for doesn&apos;t exist.</p>
            <Link href="/search" className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl gradient-accent text-white font-semibold">
              <ArrowLeft className="w-4 h-4" /> Back to Search
            </Link>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  const maxPower = Math.max(...station.chargers.map((c) => c.powerKw));
  const minPrice = Math.min(...station.chargers.map((c) => c.pricePerKwh ?? Infinity));
  const availableChargers = station.chargers.filter((c) => c.status === "available").length;
  const connectorTypes = [...new Set(station.chargers.map((c) => c.connectorType))];

  const statusConfig: Record<string, { label: string; class: string; color: string }> = {
    available: { label: "Available", class: "badge-available", color: "text-ev-green-500" },
    in_use: { label: "In Use", class: "badge-busy", color: "text-amber-500" },
    offline: { label: "Offline", class: "badge-offline", color: "text-red-500" },
    maintenance: { label: "Maintenance", class: "badge-offline", color: "text-gray-500" },
  };

  // Mock nearby places for demonstration
  const nearbyPlaces = [
    { icon: <UtensilsCrossed className="w-4 h-4" />, name: "Local Restaurant", distance: "150m", type: "restaurant" },
    { icon: <Coffee className="w-4 h-4" />, name: "Chai Point", distance: "200m", type: "tea_stall" },
    { icon: <Hotel className="w-4 h-4" />, name: "Hotel Nearby", distance: "500m", type: "hotel" },
    { icon: <Hospital className="w-4 h-4" />, name: "City Hospital", distance: "1.2 km", type: "hospital" },
    { icon: <Fuel className="w-4 h-4" />, name: "Petrol Pump", distance: "300m", type: "petrol_pump" },
    { icon: <CreditCard className="w-4 h-4" />, name: "SBI ATM", distance: "250m", type: "atm" },
    { icon: <ShoppingBag className="w-4 h-4" />, name: "Local Market", distance: "400m", type: "shopping" },
    { icon: <Landmark className="w-4 h-4" />, name: "Temple", distance: "800m", type: "temple" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      {/* Breadcrumbs */}
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 py-3 w-full" aria-label="Breadcrumb">
        <ol className="flex items-center gap-1.5 text-sm text-[var(--text-tertiary)]">
          <li><Link href="/" className="hover:text-[var(--accent)]">Home</Link></li>
          <li><ChevronRight className="w-3.5 h-3.5" /></li>
          <li><Link href="/search" className="hover:text-[var(--accent)]">Chargers</Link></li>
          <li><ChevronRight className="w-3.5 h-3.5" /></li>
          <li><Link href={`/search?q=${station.state}`} className="hover:text-[var(--accent)]">{station.state}</Link></li>
          <li><ChevronRight className="w-3.5 h-3.5" /></li>
          <li><Link href={`/search?q=${station.city}`} className="hover:text-[var(--accent)]">{station.city}</Link></li>
          <li><ChevronRight className="w-3.5 h-3.5" /></li>
          <li className="text-[var(--text-primary)] font-medium truncate max-w-[200px]">{station.name}</li>
        </ol>
      </nav>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 pb-12 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Station Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Station Header */}
            <div className="card p-6" id="station-header">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge ${station.status === "available" ? "badge-available" : station.status === "busy" ? "badge-busy" : "badge-offline"}`}>
                      {availableChargers}/{station.chargers.length} Available
                    </span>
                    {station.isVerified && (
                      <span className="flex items-center gap-1 text-xs font-semibold text-[var(--accent)]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                      </span>
                    )}
                  </div>
                  <h1 className="text-2xl md:text-3xl font-bold text-[var(--text-primary)]">
                    {station.name}
                  </h1>
                  <div className="flex items-center gap-1.5 mt-2 text-[var(--text-secondary)]">
                    <MapPin className="w-4 h-4 shrink-0" />
                    <span>{station.addressLine1}, {station.city}, {station.state} {station.pinCode}</span>
                  </div>
                  {station.operator && (
                    <p className="text-sm text-[var(--text-tertiary)] mt-1">
                      Operated by <span className="font-semibold text-[var(--text-secondary)]">{station.operator.name}</span>
                    </p>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[var(--border-primary)]">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-amber-400">
                    <Star className="w-5 h-5" fill="currentColor" />
                    <span className="text-xl font-bold text-[var(--text-primary)]">{station.avgRating}</span>
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">{station.reviewCount} reviews</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-[var(--accent)]">
                    <BatteryCharging className="w-5 h-5" />
                    <span className="text-xl font-bold text-[var(--text-primary)]">{maxPower}</span>
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">kW Max Power</p>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-[var(--text-primary)]">
                    ₹{minPrice < Infinity ? minPrice : "—"}
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">per kWh from</p>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-[var(--text-primary)]">
                    {station.chargers.length}
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">Charging Points</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-2 mt-6">
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${station.latitude},${station.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all"
                  id="get-directions-btn"
                >
                  <Navigation className="w-4 h-4" /> Get Directions
                </a>
                <button className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold border border-[var(--border-primary)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors" id="share-btn">
                  <Share2 className="w-4 h-4" /> Share
                </button>
                <button
                  onClick={toggleFavorite}
                  disabled={favoriteBusy}
                  aria-pressed={isFavorite}
                  className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold border border-[var(--border-primary)] hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-60 ${isFavorite ? "text-red-500" : "text-[var(--text-primary)]"}`}
                  id="favorite-btn"
                >
                  <Heart className={`w-4 h-4 ${isFavorite ? "text-red-500" : ""}`} fill={isFavorite ? "currentColor" : "none"} />
                  {isFavorite ? "Favorited" : "Favorite"}
                </button>
                <button className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold border border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors" id="suggest-edit-btn">
                  <Edit className="w-4 h-4" /> Suggest Edit
                </button>
              </div>
            </div>

            {/* Chargers Table */}
            <div className="card p-6" id="chargers-section">
              <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-[var(--accent)]" /> Available Chargers
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-primary)]">
                      <th className="text-left py-3 px-2 text-[var(--text-tertiary)] font-medium">Connector</th>
                      <th className="text-left py-3 px-2 text-[var(--text-tertiary)] font-medium">Power</th>
                      <th className="text-left py-3 px-2 text-[var(--text-tertiary)] font-medium">Price</th>
                      <th className="text-left py-3 px-2 text-[var(--text-tertiary)] font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {station.chargers.map((charger) => {
                      const sc = statusConfig[charger.status] || statusConfig.offline;
                      return (
                        <tr key={charger.id} className="border-b border-[var(--border-primary)] last:border-0 hover:bg-[var(--bg-secondary)] transition-colors">
                          <td className="py-3 px-2">
                            <div className="flex items-center gap-2">
                              <span className="connector-icon">{charger.connectorType.replace("Bharat", "B.")}</span>
                              <span className="font-medium text-[var(--text-primary)]">{charger.connectorType}</span>
                            </div>
                          </td>
                          <td className="py-3 px-2">
                            <span className="font-semibold text-[var(--text-primary)]">{charger.powerKw} kW</span>
                          </td>
                          <td className="py-3 px-2">
                            {charger.pricePerKwh ? (
                              <span className="font-semibold text-[var(--accent)]">₹{charger.pricePerKwh}/kWh</span>
                            ) : (
                              <span className="text-[var(--text-tertiary)]">—</span>
                            )}
                          </td>
                          <td className="py-3 px-2">
                            <span className={`badge ${sc.class}`}>{sc.label}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Features & Info */}
            <div className="card p-6" id="features-section">
              <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4">Station Features</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {station.is24x7 && (
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="w-4 h-4 text-[var(--accent)]" />
                    <span className="text-[var(--text-primary)]">Open 24×7</span>
                  </div>
                )}
                {station.freeParking && (
                  <div className="flex items-center gap-2 text-sm">
                    <ParkingCircle className="w-4 h-4 text-[var(--accent)]" />
                    <span className="text-[var(--text-primary)]">Free Parking</span>
                  </div>
                )}
                {station.isVerified && (
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-[var(--accent)]" />
                    <span className="text-[var(--text-primary)]">Verified Station</span>
                  </div>
                )}
                {connectorTypes.map((ct) => (
                  <div key={ct} className="flex items-center gap-2 text-sm">
                    <Zap className="w-4 h-4 text-navy-400" />
                    <span className="text-[var(--text-primary)]">{ct}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Nearby Places */}
            <div className="card p-6" id="nearby-section">
              <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4">Nearby Places</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {nearbyPlaces.map((place) => (
                  <div
                    key={place.name}
                    className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
                  >
                    <div className="w-9 h-9 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)]">
                      {place.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--text-primary)] truncate">{place.name}</p>
                      <p className="text-xs text-[var(--text-tertiary)]">{place.distance}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Reviews */}
            <ReviewsSection
              stationSlug={station.slug}
              avgRating={station.avgRating}
              reviewCount={station.reviewCount}
            />
          </div>

          {/* Right Column - Map & Quick Info */}
          <div className="space-y-6">
            {/* Mini Map */}
            <div className="card overflow-hidden" id="station-map">
              <div className="h-[250px]">
                <MapView
                  stations={[station]}
                  interactive={false}
                  className="rounded-none"
                />
              </div>
              <div className="p-4">
                <p className="text-xs text-[var(--text-tertiary)]">
                  {station.latitude.toFixed(4)}°N, {station.longitude.toFixed(4)}°E
                </p>
              </div>
            </div>

            {/* Contact */}
            {(station.phone || station.email || station.operator?.website) && (
              <div className="card p-4 space-y-3" id="contact-section">
                <h3 className="font-semibold text-[var(--text-primary)]">Contact</h3>
                {station.operator?.supportPhone && (
                  <a href={`tel:${station.operator.supportPhone}`} className="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--accent)]">
                    <Phone className="w-4 h-4" /> {station.operator.supportPhone}
                  </a>
                )}
                {station.operator?.website && (
                  <a href={station.operator.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--accent)]">
                    <Globe className="w-4 h-4" /> {station.operator.name} Website
                  </a>
                )}
              </div>
            )}

            {/* Report Issue */}
            <div className="card p-4" id="report-section">
              <button className="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-red-500 transition-colors w-full">
                <AlertTriangle className="w-4 h-4" /> Report a Problem
              </button>
            </div>

            {/* FAQ */}
            <div className="card p-4 space-y-3" id="faq-section">
              <h3 className="font-semibold text-[var(--text-primary)]">FAQ</h3>
              {[
                { q: "What connectors are available?", a: connectorTypes.join(", ") },
                { q: "Is parking free?", a: station.freeParking ? "Yes, free parking is available." : "No, parking charges may apply." },
                { q: "Is it open 24/7?", a: station.is24x7 ? "Yes, this station is open 24×7." : "Please check opening hours." },
              ].map((faq, i) => (
                <details key={i} className="group">
                  <summary className="text-sm font-medium text-[var(--text-primary)] cursor-pointer list-none flex items-center justify-between">
                    {faq.q}
                    <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)] group-open:rotate-90 transition-transform" />
                  </summary>
                  <p className="text-sm text-[var(--text-secondary)] mt-1 pl-0">{faq.a}</p>
                </details>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Schema.org Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "EvChargingStation",
            name: station.name,
            description: `EV charging station at ${station.addressLine1}, ${station.city}, ${station.state}`,
            address: {
              "@type": "PostalAddress",
              streetAddress: station.addressLine1,
              addressLocality: station.city,
              addressRegion: station.state,
              postalCode: station.pinCode,
              addressCountry: "IN",
            },
            geo: {
              "@type": "GeoCoordinates",
              latitude: station.latitude,
              longitude: station.longitude,
            },
            aggregateRating: {
              "@type": "AggregateRating",
              ratingValue: station.avgRating,
              reviewCount: station.reviewCount,
              bestRating: 5,
            },
            openingHoursSpecification: station.is24x7
              ? { "@type": "OpeningHoursSpecification", dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], opens: "00:00", closes: "23:59" }
              : undefined,
            amenityFeature: [
              station.freeParking && { "@type": "LocationFeatureSpecification", name: "Free Parking", value: true },
            ].filter(Boolean),
          }),
        }}
      />

      <Footer />
    </div>
  );
}

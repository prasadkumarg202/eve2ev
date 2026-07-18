/* ================================================================
   Ev2Ev — Route Planner Page
   Plan EV trips with charging stop calculations
   ================================================================ */

"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { useI18n } from "@/lib/i18n";
import { useStations } from "@/hooks/useStations";
import StationCard from "@/components/station/StationCard";
import {
  Route, MapPin, Battery, Car, Zap, Clock, IndianRupee,
  Navigation, ChevronRight, ArrowRight, Sparkles, AlertCircle
} from "lucide-react";
import { VEHICLE_TYPES } from "@/lib/utils/constants";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

export default function RoutePlannerPage() {
  const { t } = useI18n();
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [batteryPercent, setBatteryPercent] = useState(80);
  const [batteryCapacity, setBatteryCapacity] = useState(40);
  const [vehicleType, setVehicleType] = useState("car");
  const [showResults, setShowResults] = useState(false);

  const { allStations } = useStations();

  // Simulated route calculation
  const handlePlanRoute = () => {
    if (source && destination) {
      setShowResults(true);
    }
  };

  // Mock route data for demonstration
  const routeStops = allStations.slice(0, 3);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero */}
        <div className="gradient-hero py-12 md:py-16 relative overflow-hidden">
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-10 right-20 w-60 h-60 bg-ev-green-500/10 rounded-full blur-3xl animate-float" />
          </div>

          <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-ev-green-500/15 text-ev-green-400 border border-ev-green-500/20 mb-4">
              <Sparkles className="w-3.5 h-3.5" /> AI-Powered Route Planning
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
              {t("home.cta.title")}
            </h1>
            <p className="text-gray-400 max-w-xl mx-auto">
              Enter your source, destination, and vehicle details. We&apos;ll calculate the optimal charging stops.
            </p>
          </div>
        </div>

        {/* Planner Form */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 -mt-8 relative z-10">
          <div className="card p-6 md:p-8 shadow-xl" id="route-planner-form">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Source */}
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Source</label>
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] focus-within:border-[var(--accent)] transition-colors">
                  <div className="w-3 h-3 rounded-full bg-ev-green-500" />
                  <input
                    type="text"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    placeholder="e.g., Hyderabad"
                    className="w-full bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] text-sm focus:outline-none"
                    id="source-input"
                  />
                </div>
              </div>

              {/* Destination */}
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Destination</label>
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] focus-within:border-[var(--accent)] transition-colors">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <input
                    type="text"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    placeholder="e.g., Vizag"
                    className="w-full bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] text-sm focus:outline-none"
                    id="destination-input"
                  />
                </div>
              </div>

              {/* Battery Percentage */}
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                  Current Battery: {batteryPercent}%
                </label>
                <input
                  type="range"
                  min={5}
                  max={100}
                  value={batteryPercent}
                  onChange={(e) => setBatteryPercent(Number(e.target.value))}
                  className="w-full accent-[var(--accent)]"
                  id="battery-slider"
                />
                <div className="flex justify-between text-xs text-[var(--text-tertiary)] mt-1">
                  <span>5%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Battery Capacity */}
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Battery Capacity (kWh)</label>
                <input
                  type="number"
                  value={batteryCapacity}
                  onChange={(e) => setBatteryCapacity(Number(e.target.value))}
                  placeholder="40"
                  className="w-full px-4 py-3 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--accent)]"
                  id="capacity-input"
                />
              </div>

              {/* Vehicle Type */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Vehicle Type</label>
                <div className="flex flex-wrap gap-2">
                  {VEHICLE_TYPES.map((vt) => (
                    <button
                      key={vt.value}
                      onClick={() => setVehicleType(vt.value)}
                      className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                        vehicleType === vt.value
                          ? "border-[var(--accent)] text-[var(--accent)] bg-[var(--accent-light)]"
                          : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--text-tertiary)]"
                      }`}
                    >
                      <span>{vt.icon}</span> {vt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={handlePlanRoute}
              className="w-full mt-6 flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all hover:scale-[1.01]"
              id="plan-route-btn"
            >
              <Route className="w-5 h-5" /> Plan My Route
            </button>
          </div>
        </div>

        {/* Results */}
        {showResults && (
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 animate-slide-up">
            {/* Route Summary */}
            <div className="card p-6 mb-6" id="route-summary">
              <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4">Route Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <Navigation className="w-5 h-5 text-[var(--accent)] mx-auto mb-1" />
                  <div className="text-lg font-bold text-[var(--text-primary)]">620 km</div>
                  <div className="text-xs text-[var(--text-tertiary)]">Total Distance</div>
                </div>
                <div className="text-center p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <Clock className="w-5 h-5 text-navy-400 mx-auto mb-1" />
                  <div className="text-lg font-bold text-[var(--text-primary)]">9h 30m</div>
                  <div className="text-xs text-[var(--text-tertiary)]">Total Time</div>
                </div>
                <div className="text-center p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <Zap className="w-5 h-5 text-amber-400 mx-auto mb-1" />
                  <div className="text-lg font-bold text-[var(--text-primary)]">2 stops</div>
                  <div className="text-xs text-[var(--text-tertiary)]">Charging Stops</div>
                </div>
                <div className="text-center p-3 rounded-xl bg-[var(--bg-secondary)]">
                  <IndianRupee className="w-5 h-5 text-ev-green-400 mx-auto mb-1" />
                  <div className="text-lg font-bold text-[var(--text-primary)]">₹840</div>
                  <div className="text-xs text-[var(--text-tertiary)]">Est. Charging Cost</div>
                </div>
              </div>
            </div>

            {/* Route Map */}
            <div className="h-[300px] rounded-2xl overflow-hidden border border-[var(--border-primary)] mb-6">
              <MapView stations={routeStops} />
            </div>

            {/* Charging Stops */}
            <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Recommended Charging Stops</h3>
            <div className="space-y-4">
              {routeStops.map((station, i) => (
                <div key={station.id} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full gradient-accent text-white flex items-center justify-center text-sm font-bold">
                      {i + 1}
                    </div>
                    {i < routeStops.length - 1 && (
                      <div className="w-px h-16 bg-[var(--border-primary)] my-1" />
                    )}
                  </div>
                  <div className="flex-1">
                    <StationCard station={station} compact />
                  </div>
                </div>
              ))}
            </div>

            {/* AI Tip */}
            <div className="card p-4 mt-6 border-[var(--accent)]/30 bg-[var(--accent-light)]">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-[var(--accent)] shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm text-[var(--text-primary)]">AI Tip</p>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">
                    Start charging at 15-20% battery for optimal charging speed. CCS2 chargers above 50kW offer the fastest charging on this route.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

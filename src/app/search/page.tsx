/* ================================================================
   Ev2Ev — Search Page
   Full-featured search with map + list view, filters, and results
   ================================================================ */

"use client";

import { useState, useCallback, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useI18n } from "@/lib/i18n";
import { useStations } from "@/hooks/useStations";
import { useAppStore } from "@/lib/store";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import StationCard from "@/components/station/StationCard";
import type { SearchFilters, ConnectorType, StationStatus } from "@/lib/types/station";
import {
  Search, SlidersHorizontal, X, Map, List, ChevronDown,
  Zap, Car, Plug, Signal, DollarSign, Star, Clock,
  ParkingCircle, Building2
} from "lucide-react";
import { CONNECTOR_TYPES, OPERATORS_LIST, POWER_LEVELS } from "@/lib/utils/constants";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

function SearchPageContent() {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const { isMapView, setMapView, isFilterPanelOpen, setFilterPanelOpen } = useAppStore();

  const initialQuery = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState<SearchFilters>({
    query: initialQuery,
    sortBy: "rating",
    limit: 50,
  });

  // Filter state
  const [selectedConnectors, setSelectedConnectors] = useState<ConnectorType[]>([]);
  const [selectedAvailability, setSelectedAvailability] = useState<StationStatus[]>([]);
  const [selectedOperators, setSelectedOperators] = useState<string[]>([]);
  const [minRating, setMinRating] = useState<number>(0);
  const [is24x7, setIs24x7] = useState(false);
  const [freeParking, setFreeParking] = useState(false);
  const [sortBy, setSortBy] = useState<"distance" | "rating" | "price" | "power">("rating");

  // Apply filters
  useEffect(() => {
    setFilters({
      query,
      connectorTypes: selectedConnectors.length > 0 ? selectedConnectors : undefined,
      availability: selectedAvailability.length > 0 ? selectedAvailability : undefined,
      operators: selectedOperators.length > 0 ? selectedOperators : undefined,
      minRating: minRating > 0 ? minRating : undefined,
      is24x7: is24x7 || undefined,
      freeParking: freeParking || undefined,
      sortBy,
      limit: 100,
    });
  }, [query, selectedConnectors, selectedAvailability, selectedOperators, minRating, is24x7, freeParking, sortBy]);

  const { stations, filteredStations, total } = useStations(filters);

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setFilters((f) => ({ ...f, query }));
  }, [query]);

  const clearFilters = useCallback(() => {
    setSelectedConnectors([]);
    setSelectedAvailability([]);
    setSelectedOperators([]);
    setMinRating(0);
    setIs24x7(false);
    setFreeParking(false);
    setSortBy("rating");
  }, []);

  const hasActiveFilters = selectedConnectors.length > 0 || selectedAvailability.length > 0 || selectedOperators.length > 0 || minRating > 0 || is24x7 || freeParking;

  const toggleConnector = (ct: ConnectorType) => {
    setSelectedConnectors((prev) =>
      prev.includes(ct) ? prev.filter((c) => c !== ct) : [...prev, ct]
    );
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <div className="flex-1 flex flex-col">
        {/* Search Bar */}
        <div className="border-b border-[var(--border-primary)] bg-[var(--bg-primary)]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <form onSubmit={handleSearch} className="flex items-center gap-3">
              <div className="flex-1 flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] focus-within:border-[var(--accent)] transition-colors">
                <Search className="w-4 h-4 text-[var(--text-tertiary)] shrink-0" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t("home.searchPlaceholder")}
                  className="w-full bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] text-sm focus:outline-none"
                  id="search-input"
                />
                {query && (
                  <button type="button" onClick={() => setQuery("")} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              <button
                type="button"
                onClick={() => setFilterPanelOpen(!isFilterPanelOpen)}
                className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium border transition-colors ${
                  isFilterPanelOpen || hasActiveFilters
                    ? "border-[var(--accent)] text-[var(--accent)] bg-[var(--accent-light)]"
                    : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
                }`}
                id="filter-toggle"
              >
                <SlidersHorizontal className="w-4 h-4" />
                {t("search.filters")}
                {hasActiveFilters && (
                  <span className="w-5 h-5 rounded-full bg-[var(--accent)] text-white text-xs flex items-center justify-center">
                    {[selectedConnectors.length, selectedAvailability.length, selectedOperators.length, minRating > 0 ? 1 : 0, is24x7 ? 1 : 0, freeParking ? 1 : 0].reduce((a, b) => a + (b > 0 ? 1 : 0), 0)}
                  </span>
                )}
              </button>

              {/* View Toggle */}
              <div className="hidden md:flex items-center rounded-xl border border-[var(--border-primary)] overflow-hidden">
                <button
                  onClick={() => setMapView(true)}
                  className={`p-2.5 transition-colors ${isMapView ? "bg-[var(--accent)] text-white" : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"}`}
                  aria-label="Map view"
                >
                  <Map className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setMapView(false)}
                  className={`p-2.5 transition-colors ${!isMapView ? "bg-[var(--accent)] text-white" : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"}`}
                  aria-label="List view"
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </form>

            {/* Results count & sort */}
            <div className="flex items-center justify-between mt-3">
              <p className="text-sm text-[var(--text-secondary)]">
                <span className="font-semibold text-[var(--text-primary)]">{total}</span> {t("search.results")}
                {query && <span> for &ldquo;<span className="font-medium text-[var(--text-primary)]">{query}</span>&rdquo;</span>}
              </p>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--text-tertiary)]">{t("search.sortBy")}:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="text-xs bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg px-2 py-1 text-[var(--text-primary)] focus:outline-none"
                  id="sort-select"
                >
                  <option value="rating">{t("search.rating")}</option>
                  <option value="price">{t("search.price")}</option>
                  <option value="power">{t("search.power")}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Filter Panel */}
        {isFilterPanelOpen && (
          <div className="border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] animate-slide-down">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm text-[var(--text-primary)]">{t("search.filters")}</h3>
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="text-xs text-[var(--accent)] hover:underline">
                    {t("search.clearAll")}
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {/* Connectors */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)] mb-2">{t("search.connectorType")}</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {CONNECTOR_TYPES.map((ct) => (
                      <button
                        key={ct.value}
                        onClick={() => toggleConnector(ct.value as ConnectorType)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                          selectedConnectors.includes(ct.value as ConnectorType)
                            ? "border-[var(--accent)] text-[var(--accent)] bg-[var(--accent-light)]"
                            : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--text-tertiary)]"
                        }`}
                      >
                        {ct.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Availability */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)] mb-2">{t("search.availability")}</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(["available", "busy", "offline"] as StationStatus[]).map((status) => (
                      <button
                        key={status}
                        onClick={() =>
                          setSelectedAvailability((prev) =>
                            prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
                          )
                        }
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                          selectedAvailability.includes(status)
                            ? "border-[var(--accent)] text-[var(--accent)] bg-[var(--accent-light)]"
                            : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--text-tertiary)]"
                        }`}
                      >
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Toggles */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)] mb-2">Features</h4>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={is24x7} onChange={() => setIs24x7(!is24x7)} className="rounded border-[var(--border-primary)] accent-[var(--accent)]" />
                      <span className="text-sm text-[var(--text-secondary)]">{t("search.is24x7")}</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={freeParking} onChange={() => setFreeParking(!freeParking)} className="rounded border-[var(--border-primary)] accent-[var(--accent)]" />
                      <span className="text-sm text-[var(--text-secondary)]">{t("search.freeParking")}</span>
                    </label>
                  </div>
                </div>

                {/* Rating */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)] mb-2">{t("search.rating")}</h4>
                  <div className="flex gap-1.5">
                    {[0, 3, 3.5, 4, 4.5].map((r) => (
                      <button
                        key={r}
                        onClick={() => setMinRating(r)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                          minRating === r
                            ? "border-[var(--accent)] text-[var(--accent)] bg-[var(--accent-light)]"
                            : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--text-tertiary)]"
                        }`}
                      >
                        {r === 0 ? "All" : `${r}+`}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        <div className="flex-1">
          {isMapView ? (
            <div className="flex h-[calc(100vh-220px)]">
              {/* Map */}
              <div className="flex-1">
                <MapView stations={filteredStations} />
              </div>
              {/* Side Panel */}
              <div className="hidden lg:block w-96 border-l border-[var(--border-primary)] overflow-y-auto bg-[var(--bg-primary)]">
                <div className="p-4 space-y-3">
                  {stations.map((station) => (
                    <StationCard key={station.id} station={station} compact />
                  ))}
                  {stations.length === 0 && (
                    <div className="text-center py-12">
                      <Zap className="w-12 h-12 text-[var(--text-tertiary)] mx-auto mb-3" />
                      <p className="font-semibold text-[var(--text-primary)]">{t("search.noResults")}</p>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{t("search.noResultsDesc")}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {stations.map((station) => (
                  <StationCard key={station.id} station={station} />
                ))}
              </div>
              {stations.length === 0 && (
                <div className="text-center py-20">
                  <Zap className="w-16 h-16 text-[var(--text-tertiary)] mx-auto mb-4" />
                  <p className="text-xl font-semibold text-[var(--text-primary)]">{t("search.noResults")}</p>
                  <p className="text-[var(--text-secondary)] mt-2">{t("search.noResultsDesc")}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {!isMapView && <Footer />}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-3 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  );
}

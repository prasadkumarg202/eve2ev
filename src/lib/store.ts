/* ================================================================
   Ev2Ev — Global Store (Zustand)
   Manages map state, search filters, and UI state
   ================================================================ */

import { create } from "zustand";
import type { SearchFilters, ChargingStation } from "@/lib/types/station";

interface AppState {
  // Map
  mapCenter: { lat: number; lng: number };
  mapZoom: number;
  setMapCenter: (center: { lat: number; lng: number }) => void;
  setMapZoom: (zoom: number) => void;

  // Search
  searchQuery: string;
  searchFilters: SearchFilters;
  setSearchQuery: (query: string) => void;
  setSearchFilters: (filters: Partial<SearchFilters>) => void;
  resetFilters: () => void;

  // Selected station
  selectedStation: ChargingStation | null;
  setSelectedStation: (station: ChargingStation | null) => void;

  // UI
  isMobileMenuOpen: boolean;
  isFilterPanelOpen: boolean;
  isMapView: boolean;
  setMobileMenuOpen: (open: boolean) => void;
  setFilterPanelOpen: (open: boolean) => void;
  setMapView: (mapView: boolean) => void;
}

const defaultFilters: SearchFilters = {
  page: 1,
  limit: 20,
  sortBy: "distance",
};

export const useAppStore = create<AppState>((set) => ({
  // Map
  mapCenter: { lat: 20.5937, lng: 78.9629 },
  mapZoom: 5,
  setMapCenter: (center) => set({ mapCenter: center }),
  setMapZoom: (zoom) => set({ mapZoom: zoom }),

  // Search
  searchQuery: "",
  searchFilters: defaultFilters,
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSearchFilters: (filters) =>
    set((state) => ({
      searchFilters: { ...state.searchFilters, ...filters },
    })),
  resetFilters: () => set({ searchFilters: defaultFilters }),

  // Selected station
  selectedStation: null,
  setSelectedStation: (station) => set({ selectedStation: station }),

  // UI
  isMobileMenuOpen: false,
  isFilterPanelOpen: false,
  isMapView: true,
  setMobileMenuOpen: (open) => set({ isMobileMenuOpen: open }),
  setFilterPanelOpen: (open) => set({ isFilterPanelOpen: open }),
  setMapView: (mapView) => set({ isMapView: mapView }),
}));

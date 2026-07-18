/* ================================================================
   Ev2Ev — Station Data Hook
   Client-side data access with filtering, search, and geospatial queries.
   Uses seed data for initial development; will be replaced with API calls.
   ================================================================ */

"use client";

import { useMemo, useState, useCallback } from "react";
import { generateSeedStations } from "@/lib/data/seed-stations";
import type { ChargingStation, SearchFilters } from "@/lib/types/station";

// Generate stations once (module-level singleton)
let _stations: ChargingStation[] | null = null;
function getStations(): ChargingStation[] {
  if (!_stations) {
    _stations = generateSeedStations();
  }
  return _stations;
}

function haversineDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371; // km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function useStations(filters?: SearchFilters) {
  const stations = getStations();

  const filtered = useMemo(() => {
    let result = [...stations];

    if (filters?.query) {
      const q = filters.query.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.city.toLowerCase().includes(q) ||
          s.state.toLowerCase().includes(q) ||
          s.addressLine1.toLowerCase().includes(q) ||
          s.pinCode?.includes(q) ||
          s.operator?.name.toLowerCase().includes(q)
      );
    }

    if (filters?.connectorTypes?.length) {
      result = result.filter((s) =>
        s.chargers.some((c) =>
          filters.connectorTypes!.includes(c.connectorType)
        )
      );
    }

    if (filters?.availability?.length) {
      result = result.filter((s) =>
        filters.availability!.includes(s.status)
      );
    }

    if (filters?.powerRange) {
      result = result.filter((s) =>
        s.chargers.some(
          (c) =>
            c.powerKw >= filters.powerRange!.min &&
            c.powerKw <= filters.powerRange!.max
        )
      );
    }

    if (filters?.operators?.length) {
      result = result.filter(
        (s) => s.operator && filters.operators!.includes(s.operator.name)
      );
    }

    if (filters?.minRating) {
      result = result.filter((s) => s.avgRating >= filters.minRating!);
    }

    if (filters?.is24x7) {
      result = result.filter((s) => s.is24x7);
    }

    if (filters?.freeParking) {
      result = result.filter((s) => s.freeParking);
    }

    // Sort
    if (filters?.lat && filters?.lng) {
      result = result.map((s) => ({
        ...s,
        _distance: haversineDistance(filters.lat!, filters.lng!, s.latitude, s.longitude),
      }));

      if (filters?.radius) {
        result = result.filter(
          (s) => (s as ChargingStation & { _distance: number })._distance <= filters.radius!
        );
      }
    }

    switch (filters?.sortBy) {
      case "distance":
        if (filters?.lat && filters?.lng) {
          result.sort(
            (a, b) =>
              ((a as ChargingStation & { _distance?: number })._distance ?? Infinity) -
              ((b as ChargingStation & { _distance?: number })._distance ?? Infinity)
          );
        }
        break;
      case "rating":
        result.sort((a, b) => b.avgRating - a.avgRating);
        break;
      case "price":
        result.sort((a, b) => {
          const priceA = Math.min(...a.chargers.map((c) => c.pricePerKwh ?? Infinity));
          const priceB = Math.min(...b.chargers.map((c) => c.pricePerKwh ?? Infinity));
          return priceA - priceB;
        });
        break;
      case "power":
        result.sort((a, b) => {
          const powerA = Math.max(...a.chargers.map((c) => c.powerKw));
          const powerB = Math.max(...b.chargers.map((c) => c.powerKw));
          return powerB - powerA;
        });
        break;
      default:
        result.sort((a, b) => b.avgRating - a.avgRating);
    }

    return result;
  }, [stations, filters]);

  const page = filters?.page ?? 1;
  const limit = filters?.limit ?? 20;
  const paginated = filtered.slice((page - 1) * limit, page * limit);

  return {
    stations: paginated,
    allStations: stations,
    filteredStations: filtered,
    total: filtered.length,
    page,
    limit,
    totalPages: Math.ceil(filtered.length / limit),
  };
}

export function useStation(slug: string): ChargingStation | undefined {
  const stations = getStations();
  return useMemo(() => stations.find((s) => s.slug === slug), [stations, slug]);
}

export function useNearbyStations(lat: number, lng: number, radius: number = 50, limit: number = 10): ChargingStation[] {
  const stations = getStations();
  return useMemo(() => {
    return stations
      .map((s) => ({
        ...s,
        _distance: haversineDistance(lat, lng, s.latitude, s.longitude),
      }))
      .filter((s) => s._distance <= radius)
      .sort((a, b) => a._distance - b._distance)
      .slice(0, limit);
  }, [stations, lat, lng, radius, limit]);
}

export function useStationStats() {
  const stations = getStations();
  return useMemo(() => {
    const cities = new Set(stations.map((s) => s.city));
    const operators = new Set(stations.map((s) => s.operator?.name).filter(Boolean));
    const totalReviews = stations.reduce((sum, s) => sum + s.reviewCount, 0);
    const totalChargers = stations.reduce((sum, s) => sum + s.chargers.length, 0);

    return {
      stationCount: stations.length,
      cityCount: cities.size,
      operatorCount: operators.size,
      reviewCount: totalReviews,
      chargerCount: totalChargers,
    };
  }, [stations]);
}

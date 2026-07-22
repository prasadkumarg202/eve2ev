/* ================================================================
   Ev2Ev — Station data access (Supabase)

   Reads the master charging database populated by the ETL platform.
   Everything here returns the existing `ChargingStation` shape so
   components and hooks need no changes.

   If Supabase is unconfigured or holds no stations yet, callers fall
   back to bundled seed data — the app must never render an empty map
   because a backend is still being provisioned.
   ================================================================ */

import { createClient } from "./client";
import { isSupabaseConfigured } from "./env";
import type { ChargingStation, StationStatus } from "@/lib/types/station";

/** Row shape returned by the `stations_search` / `stations_nearby` RPCs. */
interface StationRow {
  id: string;
  slug: string;
  name: string;
  city: string | null;
  state: string | null;
  // `stations_nearby` returns a narrower projection than `stations_search`.
  district?: string | null;
  pin_code?: string | null;
  latitude: number;
  longitude: number;
  status: string | null;
  operator_name?: string | null;
  distance_km?: number | null;
}

const VALID_STATUS: readonly StationStatus[] = [
  "available",
  "busy",
  "offline",
  "maintenance",
];

function toStatus(value: string | null | undefined): StationStatus {
  // Guard the enum boundary: an unrecognised status from the DB must not
  // leak into `statusColors[station.status]` lookups in the UI.
  return VALID_STATUS.includes(value as StationStatus)
    ? (value as StationStatus)
    : "offline";
}

/** Map a database row onto the frontend's station model. */
export function rowToStation(row: StationRow): ChargingStation {
  const now = new Date().toISOString();
  return {
    id: row.id,
    name: row.name || "Charging Station",
    slug: row.slug,
    addressLine1: "",
    city: row.city ?? "",
    district: row.district ?? undefined,
    state: row.state ?? "",
    pinCode: row.pin_code ?? undefined,
    latitude: row.latitude,
    longitude: row.longitude,
    operator: row.operator_name
      ? {
          id: row.operator_name,
          name: row.operator_name,
          slug: row.operator_name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
          isPartner: false,
        }
      : undefined,
    is24x7: false,
    freeParking: false,
    isVerified: false,
    dataSource: "osm",
    avgRating: 0,
    reviewCount: 0,
    status: toStatus(row.status),
    // Connector/amenity detail is not yet imported — the OSM feed carries
    // it only sparsely. Empty arrays keep the UI's `.some()` filters safe.
    chargers: [],
    amenities: [],
    photos: [],
    createdAt: now,
    updatedAt: now,
  };
}

/**
 * Search stations by free text and/or an explicit area.
 *
 * `query` matches station name, city, district, state, operator or PIN,
 * with a trigram fallback so "bangalor" still matches Bengaluru.
 */
export async function searchStations(params: {
  query?: string;
  state?: string;
  city?: string;
  limit?: number;
}): Promise<ChargingStation[]> {
  if (!isSupabaseConfigured()) return [];

  const supabase = createClient();
  const { data, error } = await supabase.rpc("stations_search", {
    q: params.query?.trim() || null,
    p_state: params.state || null,
    p_city: params.city || null,
    max_results: params.limit ?? 200,
  });

  if (error) {
    console.error("[stations] search failed:", error.message);
    return [];
  }
  return (data as StationRow[]).map(rowToStation);
}

/** Stations within `radiusKm` of a point, nearest first. */
export async function nearbyStations(
  lat: number,
  lng: number,
  radiusKm = 10,
  limit = 50
): Promise<ChargingStation[]> {
  if (!isSupabaseConfigured()) return [];

  const supabase = createClient();
  const { data, error } = await supabase.rpc("stations_nearby", {
    lat,
    lng,
    radius_km: radiusKm,
    max_results: limit,
  });

  if (error) {
    console.error("[stations] nearby failed:", error.message);
    return [];
  }
  return (data as StationRow[]).map(rowToStation);
}

/** Distinct states/cities that actually have stations, for filter UI. */
export async function stationAreas(): Promise<
  { state: string; city: string | null; count: number }[]
> {
  if (!isSupabaseConfigured()) return [];

  const supabase = createClient();
  const { data, error } = await supabase.rpc("station_areas");
  if (error) {
    console.error("[stations] areas failed:", error.message);
    return [];
  }
  return (data as { state: string; city: string | null; station_count: number }[]).map(
    (r) => ({ state: r.state, city: r.city, count: r.station_count })
  );
}

/* ================================================================
   Ev2Ev — Station Card Component
   Compact card for search results and listings
   ================================================================ */

"use client";

import Link from "next/link";
import {
  MapPin, Star, Zap, Clock, ParkingCircle, CheckCircle2,
  BatteryCharging, Navigation
} from "lucide-react";
import type { ChargingStation } from "@/lib/types/station";

interface StationCardProps {
  station: ChargingStation;
  distance?: number; // km
  compact?: boolean;
}

export default function StationCard({ station, distance, compact = false }: StationCardProps) {
  const maxPower = Math.max(...station.chargers.map((c) => c.powerKw));
  const minPrice = Math.min(
    ...station.chargers.map((c) => c.pricePerKwh ?? Infinity)
  );
  const availableChargers = station.chargers.filter(
    (c) => c.status === "available"
  ).length;
  const totalChargers = station.chargers.length;
  const connectorTypes = [...new Set(station.chargers.map((c) => c.connectorType))];

  const statusColors: Record<string, string> = {
    available: "badge-available",
    busy: "badge-busy",
    offline: "badge-offline",
    maintenance: "badge-offline",
  };

  return (
    <Link
      href={`/station/${station.slug}`}
      className="card block p-4 group"
      id={`station-card-${station.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Main Info */}
        <div className="flex-1 min-w-0">
          {/* Station Name */}
          <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors truncate">
            {station.name}
          </h3>

          {/* Address */}
          <div className="flex items-center gap-1 mt-1 text-sm text-[var(--text-secondary)]">
            <MapPin className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{station.addressLine1}, {station.city}</span>
          </div>

          {/* Operator */}
          {station.operator && (
            <p className="text-xs text-[var(--text-tertiary)] mt-1">
              {station.operator.name}
            </p>
          )}
        </div>

        {/* Status Badge */}
        <span className={`badge ${statusColors[station.status] || "badge-offline"} shrink-0`}>
          {station.status === "available"
            ? `${availableChargers}/${totalChargers}`
            : station.status}
        </span>
      </div>

      {/* Stats Row */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-3">
        {/* Rating */}
        <div className="flex items-center gap-1 text-sm">
          <Star className="w-3.5 h-3.5 text-amber-400" fill="currentColor" />
          <span className="font-semibold text-[var(--text-primary)]">{station.avgRating}</span>
          <span className="text-[var(--text-tertiary)]">({station.reviewCount})</span>
        </div>

        {/* Max Power */}
        <div className="flex items-center gap-1 text-sm text-[var(--text-secondary)]">
          <BatteryCharging className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>{maxPower} kW</span>
        </div>

        {/* Price */}
        {minPrice < Infinity && (
          <div className="flex items-center gap-1 text-sm text-[var(--text-secondary)]">
            <span className="text-[var(--accent)] font-semibold">₹{minPrice}</span>
            <span>/kWh</span>
          </div>
        )}

        {/* Distance */}
        {distance !== undefined && (
          <div className="flex items-center gap-1 text-sm text-[var(--text-secondary)]">
            <Navigation className="w-3.5 h-3.5" />
            <span>{distance < 1 ? `${Math.round(distance * 1000)}m` : `${distance.toFixed(1)} km`}</span>
          </div>
        )}
      </div>

      {/* Bottom Row */}
      {!compact && (
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-[var(--border-primary)]">
          {/* Connectors */}
          <div className="flex gap-1">
            {connectorTypes.map((type) => (
              <span key={type} className="connector-icon" title={type}>
                {type.replace("Bharat", "B.")}
              </span>
            ))}
          </div>

          <div className="flex-1" />

          {/* Feature Tags */}
          {station.is24x7 && (
            <span className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
              <Clock className="w-3 h-3" /> 24×7
            </span>
          )}
          {station.freeParking && (
            <span className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
              <ParkingCircle className="w-3 h-3" /> Free P
            </span>
          )}
          {station.isVerified && (
            <span className="flex items-center gap-1 text-xs text-[var(--accent)]">
              <CheckCircle2 className="w-3 h-3" />
            </span>
          )}
        </div>
      )}
    </Link>
  );
}

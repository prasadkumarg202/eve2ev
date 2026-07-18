/* ================================================================
   Ev2Ev — MapView Component
   Interactive map with MapLibre GL JS, station markers, and clustering
   ================================================================ */

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import type { ChargingStation } from "@/lib/types/station";
import { Locate, Plus, Minus, Layers } from "lucide-react";

interface MapViewProps {
  stations: ChargingStation[];
  onStationClick?: (station: ChargingStation) => void;
  className?: string;
  interactive?: boolean;
}

export default function MapView({
  stations,
  onStationClick,
  className = "",
  interactive = true,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const { mapCenter, mapZoom, setMapCenter, setMapZoom } = useAppStore();
  const [isLoaded, setIsLoaded] = useState(false);
  const [maplibregl, setMaplibregl] = useState<typeof import("maplibre-gl") | null>(null);

  // Dynamically import maplibre-gl (browser only)
  useEffect(() => {
    import("maplibre-gl").then((mod) => {
      setMaplibregl(mod);
    });
  }, []);

  // Initialize map
  useEffect(() => {
    if (!maplibregl || !mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        name: "Ev2Ev Dark",
        sources: {
          "osm-tiles": {
            type: "raster",
            tiles: [
              "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          },
        },
        layers: [
          {
            id: "osm-tiles-layer",
            type: "raster",
            source: "osm-tiles",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [mapCenter.lng, mapCenter.lat],
      zoom: mapZoom,
      minZoom: 4,
      maxZoom: 18,
      maxBounds: [
        [60, 2],   // SW
        [100, 40],  // NE
      ],
    });

    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

    map.on("load", () => {
      setIsLoaded(true);
    });

    map.on("moveend", () => {
      const center = map.getCenter();
      setMapCenter({ lat: center.lat, lng: center.lng });
      setMapZoom(map.getZoom());
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [maplibregl]); // eslint-disable-line react-hooks/exhaustive-deps

  // Update markers when stations change
  useEffect(() => {
    if (!maplibregl || !mapRef.current || !isLoaded) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Add station markers
    stations.forEach((station) => {
      const el = document.createElement("div");
      el.className = `station-marker ${station.status}`;
      el.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`;

      el.addEventListener("click", (e) => {
        e.stopPropagation();
        onStationClick?.(station);
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([station.longitude, station.latitude])
        .addTo(mapRef.current!);

      // Popup
      const popupHtml = `
        <div style="padding: 12px; min-width: 200px;">
          <h4 style="font-weight: 600; font-size: 14px; margin: 0 0 4px 0;">${station.name}</h4>
          <p style="font-size: 12px; color: var(--text-secondary); margin: 0 0 6px 0;">${station.city}, ${station.state}</p>
          <div style="display: flex; gap: 12px; font-size: 12px;">
            <span>⭐ ${station.avgRating}</span>
            <span>⚡ ${Math.max(...station.chargers.map(c => c.powerKw))} kW</span>
            <span>₹${Math.min(...station.chargers.map(c => c.pricePerKwh ?? 0))}/kWh</span>
          </div>
          <a href="/station/${station.slug}" style="display: inline-block; margin-top: 8px; font-size: 12px; color: #10b94e; font-weight: 600; text-decoration: none;">View Details →</a>
        </div>
      `;

      const popup = new maplibregl.Popup({
        offset: 20,
        closeButton: true,
        closeOnClick: true,
        maxWidth: "280px",
      }).setHTML(popupHtml);

      marker.setPopup(popup);
      markersRef.current.push(marker);
    });
  }, [stations, isLoaded, maplibregl, onStationClick]);

  const handleLocate = useCallback(() => {
    if (!mapRef.current) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        mapRef.current?.flyTo({
          center: [pos.coords.longitude, pos.coords.latitude],
          zoom: 13,
          duration: 2000,
        });
      },
      () => {
        console.warn("Geolocation permission denied");
      }
    );
  }, []);

  const handleZoomIn = useCallback(() => {
    mapRef.current?.zoomIn({ duration: 300 });
  }, []);

  const handleZoomOut = useCallback(() => {
    mapRef.current?.zoomOut({ duration: 300 });
  }, []);

  return (
    <div className={`relative w-full h-full ${className}`}>
      {/* Map Container */}
      <div ref={mapContainer} className="w-full h-full rounded-xl overflow-hidden" id="map-container" />

      {/* Loading Overlay */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-secondary)] rounded-xl">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-3 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-[var(--text-secondary)]">Loading map...</p>
          </div>
        </div>
      )}

      {/* Map Controls */}
      {interactive && isLoaded && (
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
          <button
            onClick={handleLocate}
            className="w-10 h-10 rounded-xl glass-heavy flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors shadow-md"
            aria-label="Find my location"
            id="map-locate-btn"
          >
            <Locate className="w-5 h-5" />
          </button>
          <button
            onClick={handleZoomIn}
            className="w-10 h-10 rounded-xl glass-heavy flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors shadow-md"
            aria-label="Zoom in"
            id="map-zoom-in-btn"
          >
            <Plus className="w-5 h-5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="w-10 h-10 rounded-xl glass-heavy flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors shadow-md"
            aria-label="Zoom out"
            id="map-zoom-out-btn"
          >
            <Minus className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Station Count Badge */}
      {isLoaded && (
        <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-lg glass-heavy text-xs font-semibold text-[var(--text-secondary)] z-10">
          {stations.length} stations
        </div>
      )}
    </div>
  );
}

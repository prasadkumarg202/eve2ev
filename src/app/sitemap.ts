/* ================================================================
   Ev2Ev — Sitemap Generator
   Dynamic sitemap for all pages and stations
   ================================================================ */

import type { MetadataRoute } from "next";
import { generateSeedStations } from "@/lib/data/seed-stations";
import { INDIAN_STATES } from "@/lib/utils/constants";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://ev2ev.in";
  const stations = generateSeedStations();

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "daily", priority: 1 },
    { url: `${baseUrl}/search`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${baseUrl}/route-planner`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.8 },
    { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.7 },
    { url: `${baseUrl}/login`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
  ];

  // Station pages
  const stationPages: MetadataRoute.Sitemap = stations.map((station) => ({
    url: `${baseUrl}/station/${station.slug}`,
    lastModified: new Date(station.updatedAt),
    changeFrequency: "daily" as const,
    priority: 0.8,
  }));

  // State pages
  const statePages: MetadataRoute.Sitemap = INDIAN_STATES.map((state) => ({
    url: `${baseUrl}/explore/${state.toLowerCase().replace(/\s+/g, "-")}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));

  return [...staticPages, ...stationPages, ...statePages];
}

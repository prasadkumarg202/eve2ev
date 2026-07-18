/* ================================================================
   Ev2Ev — Robots.txt
   ================================================================ */

import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin/", "/api/", "/profile/"],
      },
    ],
    sitemap: "https://ev2ev.in/sitemap.xml",
  };
}

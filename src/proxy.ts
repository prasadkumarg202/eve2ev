/* ================================================================
   Ev2Ev — Proxy (Next.js 16 rename of `middleware`)
   Runs on every matched request to keep the Supabase auth session
   fresh. Node.js runtime only — the edge runtime is not supported in
   `proxy`. See node_modules/next/dist/docs .../file-conventions/proxy.md
   ================================================================ */

import { type NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/proxy";

export async function proxy(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, sitemap.xml, robots.txt (metadata)
     * - image assets
     */
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|manifest.json|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};

/* ================================================================
   Ev2Ev — Supabase Browser Client
   For use in Client Components ("use client"). Reads/writes the auth
   session from cookies via @supabase/ssr.
   ================================================================ */

"use client";

import { createBrowserClient } from "@supabase/ssr";
import type { Database } from "./database.types";
import { SUPABASE_URL, SUPABASE_ANON_KEY } from "./env";

/**
 * Creates a Supabase client scoped to the browser. Safe to call on every
 * render — @supabase/ssr memoizes the underlying client per set of args.
 */
export function createClient() {
  return createBrowserClient<Database>(SUPABASE_URL, SUPABASE_ANON_KEY);
}

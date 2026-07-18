/* ================================================================
   Ev2Ev — Supabase Server Client
   For use in Server Components, Route Handlers, and Server Actions.
   NOTE: Next.js 16 makes `cookies()` async — it must be awaited.
   ================================================================ */

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import type { Database } from "./database.types";
import { SUPABASE_URL, SUPABASE_ANON_KEY } from "./env";

/**
 * Creates a request-scoped Supabase client backed by the Next.js cookie store.
 * Must be awaited because `cookies()` is async in Next.js 16.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient<Database>(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          );
        } catch {
          // The `setAll` method was called from a Server Component. This can
          // be ignored when session refresh runs in `proxy.ts` (which it does).
        }
      },
    },
  });
}

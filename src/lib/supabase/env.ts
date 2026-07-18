/* ================================================================
   Ev2Ev — Supabase Environment Helpers
   Central place to read + validate Supabase env vars so the rest of
   the app can gracefully degrade to seed data when unconfigured.
   ================================================================ */

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

/**
 * True when both the Supabase URL and anon key are present. Used to decide
 * whether to hit the database or fall back to bundled seed data. This keeps
 * the app fully functional (auth pages excepted) before the backend is
 * provisioned.
 */
export function isSupabaseConfigured(): boolean {
  return Boolean(SUPABASE_URL) && Boolean(SUPABASE_ANON_KEY);
}

/**
 * Capacitor configuration for the Ev2Ev native shell (iOS / Android).
 *
 * STATUS: scaffolding only — Capacitor is NOT installed yet.
 * See MOBILE_APP.md for the full setup guide and the exact install commands.
 *
 * WHY THE LOCAL TYPE BELOW INSTEAD OF `import { CapacitorConfig } from '@capacitor/cli'`?
 * This repo's tsconfig includes every root-level .ts file, so this file is
 * type-checked by the
 * app's `tsc` even though Capacitor is not a dependency. Importing '@capacitor/cli'
 * before it is installed would break `tsc --noEmit` (and CI). The minimal structural
 * type below keeps this file self-contained and type-safe today. Once you run
 * `npm i -D @capacitor/cli` you may replace `Ev2EvCapacitorConfig` with:
 *
 *   import type { CapacitorConfig } from '@capacitor/cli';
 *
 * (The Capacitor CLI itself only reads the default export's shape at
 * `npx cap sync` time, so the local type works fine either way.)
 */

/** Minimal structural subset of Capacitor's `CapacitorConfig` used by this project. */
interface Ev2EvCapacitorConfig {
  appId: string;
  appName: string;
  /** Directory of the web assets bundled into the native app (unused in remote-URL mode, but required). */
  webDir: string;
  server?: {
    /** Remote URL the native WebView loads instead of bundled assets. */
    url?: string;
    /** Allow plain-http traffic. Keep false in production. */
    cleartext?: boolean;
    /** Hostname used for the local origin when serving bundled assets. */
    hostname?: string;
    androidScheme?: 'http' | 'https';
    iosScheme?: string;
  };
  ios?: {
    contentInset?: 'automatic' | 'scrollableAxes' | 'never' | 'always';
  };
  android?: {
    allowMixedContent?: boolean;
  };
  /** Per-plugin configuration, keyed by plugin name. */
  plugins?: Record<string, Record<string, unknown>>;
}

/**
 * The deployed PWA URL the native shell loads.
 *
 * Set NEXT_PUBLIC_APP_URL in your shell environment (or in .env, loaded however
 * you run `npx cap sync` — the Capacitor CLI does NOT load .env files itself, so
 * export it first, e.g.:
 *
 *   # PowerShell
 *   $env:NEXT_PUBLIC_APP_URL = "https://ev2ev.in"; npx cap sync
 *   # bash
 *   NEXT_PUBLIC_APP_URL=https://ev2ev.in npx cap sync
 *
 * See .env.capacitor.example. The fallback below is a placeholder — replace it
 * with the real production URL before shipping.
 */
const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? 'https://ev2ev.example.com';

const config: Ev2EvCapacitorConfig = {
  appId: 'in.ev2ev.app',
  appName: 'Ev2Ev',

  // Required by Capacitor even in remote-URL mode. `public` is a placeholder
  // containing the PWA's static assets; it is NOT a static export of the app.
  webDir: 'public',

  // ── RECOMMENDED: remote / hosted-URL wrapper ─────────────────────────────
  // Ev2Ev is a Next.js SERVER app (server components, Supabase auth cookies,
  // a proxy.ts session layer). It cannot be cleanly exported to static HTML,
  // so instead of bundling web assets, the native shell loads the deployed
  // PWA over HTTPS. Pros: one deploy updates web + native, auth "just works"
  // (same origin, same cookies). Cons: requires network; app-store reviewers
  // expect the app to feel native, so keep the PWA polished.
  server: {
    url: APP_URL,
    cleartext: false, // never allow plain HTTP in production
  },

  // ── ALTERNATIVE: bundled static-export mode (NOT currently viable) ───────
  // If the app is ever restructured so every page can be statically exported
  // (`output: 'export'` in next.config, no server components needing request
  // context, auth moved fully client-side), delete the `server` block above,
  // point webDir at the export output, and sync the bundle into the shell:
  //
  //   webDir: 'out',
  //   // no `server.url` — Capacitor serves the bundled files from
  //   // capacitor://localhost (iOS) / https://localhost (Android)
  //
  // Until then, leave this commented out — `next build` will fail with
  // `output: 'export'` because of the server/auth/proxy layer.

  // ── Plugin config stubs (uncomment after installing each plugin) ─────────
  // plugins: {
  //   SplashScreen: {
  //     launchShowDuration: 1500,
  //     launchAutoHide: true,
  //     backgroundColor: '#09090b', // matches manifest.json background_color
  //     showSpinner: false,
  //   },
  //   StatusBar: {
  //     // 'DARK' = light text on dark background — matches the app's dark UI
  //     style: 'DARK',
  //     backgroundColor: '#09090b',
  //     overlaysWebView: false,
  //   },
  // },
};

export default config;

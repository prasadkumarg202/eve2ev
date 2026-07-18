# Ev2Ev — Shipping as a Native Mobile App

Ev2Ev is a Next.js **server** app (App Router, server components, Supabase auth
with a `proxy.ts` session layer). That one fact drives every decision below:
**the app cannot be statically exported**, so the native strategy is to wrap the
*deployed* PWA, not to bundle HTML into the binary.

There are two paths. You can ship (A) first and add (B) later — they are not
mutually exclusive.

---

## Path A — PWA install / TWA (fastest)

The PWA manifest (`public/manifest.json`) and service worker already make Ev2Ev
installable from the browser on both platforms. For a **Play Store** listing
without touching native code, use a **Trusted Web Activity (TWA)**:

- **Bubblewrap** (CLI): `npm i -g @bubblewrap/cli`, then `bubblewrap init --manifest https://<your-domain>/manifest.json` and `bubblewrap build`. Produces a signed AAB you upload to Play Console.
- **PWABuilder** (web UI): go to <https://www.pwabuilder.com>, enter the deployed URL, download the generated Android package. It can also generate iOS/Windows shells, but its iOS output is itself a WebView wrapper (Apple has no TWA equivalent).
- Both require serving `/.well-known/assetlinks.json` on your domain so Android trusts the app ↔ site link (Bubblewrap/PWABuilder generate the file contents for you).

**Use Path A when:** you want a Play Store presence quickly, need no native
plugins, and browser capabilities (web geolocation, notifications on Android)
are enough. **Limitation:** no real iOS App Store path, no native plugin access,
no reliable iOS push.

## Path B — Capacitor native wrapper

A real native shell (Xcode/Android Studio projects) whose WebView loads the app.
**Use Path B when:** you want iOS App Store presence, native push notifications,
native geolocation/background behavior, or any other native plugin.

**Why the hosted-URL config:** Capacitor's default mode bundles a static `webDir`
into the binary — which requires `next export`-style static output that this app
cannot produce (server components, Supabase cookies, the proxy session layer).
Instead, `capacitor.config.ts` (already in the repo root) sets
`server: { url: <deployed PWA URL>, cleartext: false }` so the shell loads the
live HTTPS deployment. Auth cookies, server rendering, and middleware all work
exactly as on the web, and every web deploy instantly updates the "native" app.
Trade-offs: the app needs connectivity (mitigate with the service worker), and
app-store review expects native-feeling UX — handle safe areas and avoid
browser-ish chrome.

### Prerequisites

- Node 20+ (already required by the project)
- **Android:** Android Studio (latest stable) + SDK 34+, JDK 17
- **iOS:** a Mac with Xcode 15+, CocoaPods (`sudo gem install cocoapods`), an Apple Developer account for device builds/App Store

### Setup commands (run these LATER, when you're ready)

```bash
# 1. Install Capacitor (core + CLI + platforms)
npm i @capacitor/core
npm i -D @capacitor/cli
npm i @capacitor/ios @capacitor/android

# 2. Init is OPTIONAL here — capacitor.config.ts already exists with
#    appId in.ev2ev.app / appName Ev2Ev. If you run it, keep those values:
# npx cap init Ev2Ev in.ev2ev.app --web-dir public

# 3. Add the native projects (creates ios/ and android/ directories — commit them)
npx cap add ios
npx cap add android

# 4. Set the deployed URL and sync config + plugins into the native projects.
#    (The Capacitor CLI does not read .env files — export the var first.
#     See .env.capacitor.example.)
NEXT_PUBLIC_APP_URL=https://ev2ev.in npx cap sync

# 5. Open in the native IDE to run/build
npx cap open ios
npx cap open android
```

Re-run `npx cap sync` whenever you install/remove a Capacitor plugin or change
`capacitor.config.ts`. Because the shell loads the hosted URL, you do **not**
need to re-sync for ordinary web deploys.

After installing the CLI, you can switch `capacitor.config.ts` from its local
interface to the official type: `import type { CapacitorConfig } from '@capacitor/cli';`
(the file header explains why it doesn't import that today).

### The Supabase OAuth deep-link gotcha (read before enabling Google login in the app)

Google blocks OAuth inside embedded WebViews (`disallowed_useragent`), and even
when a provider allows it, the redirect back to `/auth/callback` needs to land
in *your app*, not a browser tab. The standard Capacitor pattern:

1. **Open the OAuth URL in the system browser**, not the WebView. Install
   `@capacitor/browser` and call `Browser.open({ url })` with the URL from
   `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo, skipBrowserRedirect: true } })`.
2. **Redirect back into the app via a deep link.** Use a custom scheme such as
   `in.ev2ev.app://auth/callback` as the `redirectTo`, and add it to the
   **Supabase Dashboard → Authentication → URL Configuration → Redirect URLs**
   allowlist (alongside the existing `https://<domain>/auth/callback`).
3. **Catch the deep link natively** with the App API's `appUrlOpen` listener
   (`@capacitor/app`, installed automatically with the platforms):

   ```ts
   import { App } from '@capacitor/app';
   import { Browser } from '@capacitor/browser';

   App.addListener('appUrlOpen', async ({ url }) => {
     if (url.startsWith('in.ev2ev.app://auth/callback')) {
       await Browser.close();
       // Extract the `code` param and finish the PKCE exchange,
       // e.g. supabase.auth.exchangeCodeForSession(code)
     }
   });
   ```

4. **Native registration of the scheme/links:**
   - **Android** (`android/app/src/main/AndroidManifest.xml`): an
     `<intent-filter>` on the main activity with
     `<data android:scheme="in.ev2ev.app" />` (plus `VIEW` action and
     `DEFAULT`/`BROWSABLE` categories). For *verified* HTTPS App Links instead
     of a custom scheme, add `android:autoVerify="true"` with your domain and
     serve `/.well-known/assetlinks.json` (same file TWA needs).
   - **iOS**: custom scheme via `CFBundleURLTypes` in `Info.plist`, or — better
     for production — Universal Links via the Associated Domains capability
     (`applinks:ev2ev.in` in Xcode Signing & Capabilities) plus
     `/.well-known/apple-app-site-association` served from the domain.

Note: because the shell loads the hosted URL, the WebView shares the site's
cookies, so a session established on the web origin generally carries over —
but the OAuth *round-trip* itself must still follow the pattern above.

### Native niceties to wire later

| Plugin | Purpose | Notes |
|---|---|---|
| `@capacitor/status-bar` | Style/color the status bar | Config stub already commented in `capacitor.config.ts` (dark bg `#09090b`) |
| `@capacitor/splash-screen` | Branded launch screen | Stub in config; generate assets with `@capacitor/assets` |
| `@capacitor/geolocation` | Native GPS for "near me" | The app already uses `navigator.geolocation`, which works in the WebView; switch to the plugin only if you need better permission UX or background accuracy. Requires `NSLocationWhenInUseUsageDescription` (iOS) and `ACCESS_FINE_LOCATION` (Android). |
| `@capacitor/push-notifications` | Push (FCM / APNs) | The main capability neither PWA-on-iOS nor TWA gives you fully |

**Safe areas:** the web app should use `viewport-fit=cover` and CSS
`env(safe-area-inset-top/bottom/left/right)` padding on fixed headers/footers —
this benefits the PWA on notched phones today and the Capacitor shell later.

### Store submission (high level)

- **Play Store:** Play Console account (one-time $25). Build a signed AAB in
  Android Studio (or `cd android && ./gradlew bundleRelease`), enroll in Play
  App Signing, provide privacy policy + data-safety form. WebView-wrapper apps
  are accepted; make sure the app works (offline page at minimum) without
  feeling like "just a website".
- **App Store:** Apple Developer Program ($99/yr). Archive in Xcode → upload
  via Organizer → App Store Connect. Apple's guideline 4.2 (minimum
  functionality) scrutinizes thin web wrappers — native touches (push, splash,
  proper safe areas, no browser UI) materially improve approval odds.
- Both stores require icons/screenshots per device class and a privacy policy
  URL. Location usage must be declared and justified on both.

---

## Suggested order

1. Now: ship the PWA; add safe-area CSS and a solid offline fallback.
2. Soon: Play Store via TWA (Bubblewrap/PWABuilder) — days of work, not weeks.
3. Later: Capacitor for iOS (+ optionally replace the TWA on Android for plugin
   parity), wiring the OAuth deep-link flow before enabling social login in-app.

*Commands above are current as of Capacitor 7 (mid-2026). If a command errors,
check the official docs at <https://capacitorjs.com/docs> — flags occasionally
change between major versions.*

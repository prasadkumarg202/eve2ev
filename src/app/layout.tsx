/* ================================================================
   Ev2Ev — Root Layout
   Sets up fonts, providers, metadata, and global structure
   ================================================================ */

import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers/Providers";
import MobileNav from "@/components/layout/MobileNav";
import PWAProvider from "@/components/pwa/PWAProvider";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://ev2ev.in"
  ),
  title: {
    default: "Ev2Ev — Every EV Charger in India | Find, Compare, Book",
    template: "%s | Ev2Ev",
  },
  description:
    "India's unified EV charging discovery platform. Find, compare, and book EV chargers across all operators — Tata Power, Statiq, Jio-bp, BPCL, ChargeZone, and 50+ more. Route planner, reviews, and travel guides.",
  keywords: [
    "EV charging", "electric vehicle", "charger", "India", "Tata Power",
    "Statiq", "Jio-bp", "BPCL", "CCS2", "Type 2", "fast charging",
    "route planner", "EV travel", "charging station near me",
  ],
  authors: [{ name: "Ev2Ev", url: "https://ev2ev.in" }],
  creator: "Ev2Ev",
  publisher: "Ev2Ev",
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://ev2ev.in",
    siteName: "Ev2Ev",
    title: "Ev2Ev — Every EV Charger in India",
    description:
      "Find, compare, and book EV chargers across all operators in India. Route planner, community reviews, and AI travel assistant.",
    images: [
      {
        url: "/images/og-image.png",
        width: 1200,
        height: 630,
        alt: "Ev2Ev - India's EV Charging Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Ev2Ev — Every EV Charger in India",
    description: "Find, compare, and book EV chargers across all operators.",
    images: ["/images/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  applicationName: "Ev2Ev",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    title: "Ev2Ev",
    statusBarStyle: "black-translucent",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icons/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/icons/icon-192x192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: [{ url: "/icons/apple-touch-icon.png", sizes: "180x180" }],
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full`}
      suppressHydrationWarning
    >
      <head>
        {/* Preconnect to tile servers */}
        <link rel="preconnect" href="https://a.tile.openstreetmap.org" />
        <link rel="preconnect" href="https://b.tile.openstreetmap.org" />
        {/* Schema.org structured data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebApplication",
              name: "Ev2Ev",
              description: "India's unified EV charging discovery platform",
              url: "https://ev2ev.in",
              applicationCategory: "UtilityApplication",
              operatingSystem: "Web, Android, iOS",
              offers: {
                "@type": "Offer",
                price: "0",
                priceCurrency: "INR",
              },
              author: {
                "@type": "Organization",
                name: "Ev2Ev",
              },
            }),
          }}
        />
      </head>
      <body className="min-h-full flex flex-col antialiased">
        <Providers>
          {children}
          <MobileNav />
          <PWAProvider />
        </Providers>
      </body>
    </html>
  );
}

import sharp from "sharp";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const ROOT = "d:/websites/Ev2Ev";
const ICONS = path.join(ROOT, "public/icons");
const IMAGES = path.join(ROOT, "public/images");

// Lucide "Zap" bolt path on a 24x24 grid.
const BOLT = "M13 2 3 14h9l-1 8 10-12h-9l1-8z";

// Rounded-tile icon (used for standard + apple). Bolt fills ~55%.
function tileSVG({ rounded = true, opaque = true } = {}) {
  const rx = rounded ? 112 : 0;
  const bg = opaque
    ? `<rect width="512" height="512" rx="${rx}" fill="url(#g)"/>`
    : `<rect width="512" height="512" rx="${rx}" fill="url(#g)"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#10b94e"/>
      <stop offset="1" stop-color="#047835"/>
    </linearGradient>
  </defs>
  ${bg}
  <g transform="translate(100,100) scale(13)">
    <path d="${BOLT}" fill="#ffffff" stroke="#ffffff" stroke-width="1.2" stroke-linejoin="round"/>
  </g>
</svg>`;
}

// Maskable: full-bleed gradient, bolt kept inside the 80% safe zone.
function maskableSVG() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#10b94e"/>
      <stop offset="1" stop-color="#047835"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" fill="url(#g)"/>
  <g transform="translate(136,136) scale(10)">
    <path d="${BOLT}" fill="#ffffff" stroke="#ffffff" stroke-width="1.2" stroke-linejoin="round"/>
  </g>
</svg>`;
}

// Monochrome badge (white silhouette, transparent bg) for notifications.
function badgeSVG() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <g transform="translate(100,100) scale(13)">
    <path d="${BOLT}" fill="#ffffff"/>
  </g>
</svg>`;
}

// Wide branded image (og / screenshot) — no text (avoids font deps).
function bannerSVG(w, h) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#09090b"/>
      <stop offset="1" stop-color="#064e26"/>
    </linearGradient>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#34d375"/>
      <stop offset="1" stop-color="#10b94e"/>
    </linearGradient>
  </defs>
  <rect width="${w}" height="${h}" fill="url(#bg)"/>
  <circle cx="${w * 0.5}" cy="${h * 0.5}" r="${h * 0.42}" fill="#10b94e" opacity="0.12"/>
  <g transform="translate(${w / 2 - 120},${h / 2 - 130}) scale(10)">
    <path d="${BOLT}" fill="url(#g)"/>
  </g>
</svg>`;
}

async function png(svg, size, file) {
  await sharp(Buffer.from(svg)).resize(size, size).png().toFile(file);
  return file;
}

async function main() {
  await mkdir(ICONS, { recursive: true });
  await mkdir(IMAGES, { recursive: true });

  const tile = tileSVG();
  const mask = maskableSVG();
  const badge = badgeSVG();

  const standardSizes = [72, 96, 128, 144, 152, 192, 384, 512];
  const out = [];

  for (const s of standardSizes) {
    out.push(await png(tile, s, path.join(ICONS, `icon-${s}x${s}.png`)));
  }

  // Maskable variants
  out.push(await png(mask, 192, path.join(ICONS, "maskable-192x192.png")));
  out.push(await png(mask, 512, path.join(ICONS, "maskable-512x512.png")));

  // Apple touch icon (opaque, 180)
  out.push(await png(tile, 180, path.join(ICONS, "apple-touch-icon.png")));

  // Notification icon + badge
  out.push(await png(tile, 512, path.join(ICONS, "icon.png")));
  out.push(await png(badge, 96, path.join(ICONS, "badge.png")));

  // Favicons
  out.push(await png(tile, 32, path.join(ICONS, "favicon-32x32.png")));
  out.push(await png(tile, 16, path.join(ICONS, "favicon-16x16.png")));

  // Wide branded images to satisfy manifest/layout references
  await sharp(Buffer.from(bannerSVG(1200, 630))).png().toFile(path.join(IMAGES, "og-image.png"));
  await sharp(Buffer.from(bannerSVG(1280, 720))).png().toFile(path.join(IMAGES, "screenshot-home.png"));
  // Narrow screenshot for richer install UI (mobile form factor)
  await sharp(Buffer.from(bannerSVG(720, 1280))).png().toFile(path.join(IMAGES, "screenshot-mobile.png"));

  console.log("Generated", out.length + 3, "images");
  console.log(out.map((f) => path.relative(ROOT, f)).join("\n"));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

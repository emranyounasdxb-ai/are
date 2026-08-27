import localFont from "next/font/local";

// Preserve the existing Arabic body mapping. Purchased faces are runtime-only;
// their source files are never imported into the build or public repository.
const ibmPlexSansArabic = localFont({
  display: "swap",
  src: [
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-arabic-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-arabic-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-arabic-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-arabic-700-normal.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-arabic",
});

// The Arabic subset deliberately omits Latin names, Western numerals and most
// punctuation. Put this same-family subset before the Arabic face's automatic
// system fallback so mixed-script Arabic copy never falls through to Arial.
const ibmPlexSansArabicLatin = localFont({
  display: "swap",
  preload: false,
  adjustFontFallback: false,
  src: [
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../../../node_modules/@fontsource/ibm-plex-sans-arabic/files/ibm-plex-sans-arabic-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-arabic-latin",
});

export const publicFontVariables = `are-private-fonts ${ibmPlexSansArabic.variable} ${ibmPlexSansArabicLatin.variable}`;

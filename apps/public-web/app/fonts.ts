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

export const publicFontVariables = `are-private-fonts ${ibmPlexSansArabic.variable}`;

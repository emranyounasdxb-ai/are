import { IBM_Plex_Sans_Arabic, Manrope, Playfair_Display } from "next/font/google";

const manrope = Manrope({
  display: "swap",
  subsets: ["latin"],
  variable: "--font-body-latin",
});

const playfairDisplay = Playfair_Display({
  display: "swap",
  subsets: ["latin"],
  variable: "--font-luxury-accent",
});

const ibmPlexSansArabic = IBM_Plex_Sans_Arabic({
  display: "swap",
  subsets: ["arabic"],
  variable: "--font-arabic",
  weight: ["400", "500", "600", "700"],
});

export const publicFontVariables = [
  manrope.variable,
  playfairDisplay.variable,
  ibmPlexSansArabic.variable,
].join(" ");

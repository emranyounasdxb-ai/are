import type { Metadata } from "next";
import { Manrope, Montserrat } from "next/font/google";
import type { ReactNode } from "react";

import "./globals.css";
import { Providers } from "./providers";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-admin-body" });
const montserrat = Montserrat({ subsets: ["latin"], variable: "--font-admin-heading" });

export const metadata: Metadata = {
  title: { default: "ARE Admin", template: "%s | ARE Admin" },
  robots: { index: false, follow: false, nocache: true },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" dir="ltr" className={`${manrope.variable} ${montserrat.variable}`}>
      <body><Providers>{children}</Providers></body>
    </html>
  );
}

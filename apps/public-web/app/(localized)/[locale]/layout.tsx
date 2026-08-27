import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import { MotionProvider } from "../../../components/motion/motion-provider";
import { SiteHeader } from "../../../components/navigation/site-header";
import { homeCopy, isLocale, locales } from "../../../lib/home-copy";
import { publicFontVariables } from "../../fonts";
import "../../globals.css";
import "../../private-fonts.css";

export const dynamicParams = false;

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default async function LocaleRootLayout({
  children,
  params,
}: Readonly<{
  children: ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;

  if (!isLocale(locale)) {
    notFound();
  }

  return (
    <html className={publicFontVariables} lang={locale} dir={locale === "ar" ? "rtl" : "ltr"}>
      <head>
        {locale === "en" ? <>
          <link rel="preload" href="/font-assets/v1/h1-regular.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
          <link rel="preload" href="/font-assets/v1/headings.ttf" as="font" type="font/ttf" crossOrigin="anonymous" />
          <link rel="preload" href="/font-assets/v1/body.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        </> : <link rel="preload" href="/font-assets/v1/arabic-h1.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />}
      </head>
      <body className="are-site">
        <SiteHeader copy={homeCopy[locale].header} locale={locale}/>
        <MotionProvider>{children}</MotionProvider>
      </body>
    </html>
  );
}

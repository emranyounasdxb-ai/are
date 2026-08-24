import type { ReactNode } from "react";

import { MotionProvider } from "../../components/motion/motion-provider";
import { publicFontVariables } from "../fonts";
import "../globals.css";

export default function DefaultRootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html className={publicFontVariables} lang="en" dir="ltr">
      <body className="are-site"><MotionProvider>{children}</MotionProvider></body>
    </html>
  );
}

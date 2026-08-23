"use client";

import type { ReactNode } from "react";
import { domAnimation, LazyMotion, MotionConfig } from "motion/react";
import * as m from "motion/react-m";

type RevealProps = Readonly<{
  children: ReactNode;
  className?: string;
}>;

export function Reveal({ children, className }: RevealProps) {
  return (
    <MotionConfig reducedMotion="user">
      <LazyMotion features={domAnimation} strict>
        <m.div
          className={className}
          initial={{ opacity: 0.92, y: 12 }}
          transition={{ duration: 0.42, ease: [0.16, 1, 0.3, 1] }}
          viewport={{ amount: 0.4, once: true }}
          whileInView={{ opacity: 1, y: 0 }}
        >
          {children}
        </m.div>
      </LazyMotion>
    </MotionConfig>
  );
}

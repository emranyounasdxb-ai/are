"use client";

import type { ReactNode } from "react";
import { domAnimation, LazyMotion, MotionConfig } from "motion/react";
import * as m from "motion/react-m";

type RevealProps = Readonly<{
  children: ReactNode;
  className?: string;
  delay?: number;
  distance?: number;
}>;

export function Reveal({ children, className, delay = 0, distance = 16 }: RevealProps) {
  return (
    <MotionConfig reducedMotion="user">
      <LazyMotion features={domAnimation} strict>
        <m.div
          className={className}
          initial={{ opacity: 0.82, y: distance }}
          transition={{ delay, duration: 0.56, ease: [0.16, 1, 0.3, 1] }}
          viewport={{ amount: 0.4, once: true }}
          whileInView={{ opacity: 1, y: 0 }}
        >
          {children}
        </m.div>
      </LazyMotion>
    </MotionConfig>
  );
}

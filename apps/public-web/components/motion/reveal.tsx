"use client";

import type { ReactNode } from "react";
import { useReducedMotion } from "motion/react";
import * as m from "motion/react-m";

import { cinematicEase, motionDuration } from "./tokens";

type RevealProps = Readonly<{
  children: ReactNode;
  className?: string;
  delay?: number;
  distance?: number;
}>;

export function Reveal({ children, className, delay = 0, distance = 16 }: RevealProps) {
  const reduceMotion = useReducedMotion();

  return (
    <m.div
      className={className}
      initial={reduceMotion ? { opacity: 1 } : { opacity: 0.94, y: distance }}
      transition={{
        delay: reduceMotion ? 0 : delay,
        duration: reduceMotion ? 0 : motionDuration.hero,
        ease: cinematicEase,
      }}
      viewport={{ amount: 0.22, once: true }}
      whileInView={{ opacity: 1, y: 0 }}
    >
      {children}
    </m.div>
  );
}

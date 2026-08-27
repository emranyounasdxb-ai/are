"use client";

import { useReducedMotion } from "motion/react";

import ShinyText from "../ShinyText";

export function HomeHeroShinyEyebrow({ text }: Readonly<{ text: string }>) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <span>{text}</span>;
  }

  return (
    <ShinyText
      color="#b5b5b5"
      delay={0}
      direction="left"
      pauseOnHover={false}
      shineColor="#ffffff"
      speed={2}
      spread={120}
      text={text}
      yoyo={false}
    />
  );
}

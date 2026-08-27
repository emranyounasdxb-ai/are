import type { ComponentType } from "react";

type ShinyTextProps = Readonly<{
  className?: string;
  color?: string;
  delay?: number;
  direction?: "left" | "right";
  disabled?: boolean;
  pauseOnHover?: boolean;
  shineColor?: string;
  speed?: number;
  spread?: number;
  text: string;
  yoyo?: boolean;
}>;

declare const ShinyText: ComponentType<ShinyTextProps>;

export default ShinyText;

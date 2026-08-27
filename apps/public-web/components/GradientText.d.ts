import type { ComponentType, ReactNode } from "react";

type GradientTextProps = Readonly<{
  animationSpeed?: number;
  children: ReactNode;
  className?: string;
  colors?: string[];
  direction?: "diagonal" | "horizontal" | "vertical";
  pauseOnHover?: boolean;
  showBorder?: boolean;
  yoyo?: boolean;
}>;

declare const GradientText: ComponentType<GradientTextProps>;

export default GradientText;

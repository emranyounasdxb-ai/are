import type { ElementType, HTMLAttributes, ReactElement } from "react";

export type TextTypeProps = HTMLAttributes<HTMLElement> &
  Readonly<{
    as?: ElementType;
    className?: string;
    cursorCharacter?: string;
    loop?: boolean;
    pauseDuration?: number;
    showCursor?: boolean;
    text: string | readonly string[];
    typingSpeed?: number;
  }>;

export default function TextType(props: TextTypeProps): ReactElement;

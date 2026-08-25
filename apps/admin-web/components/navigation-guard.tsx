"use client";

import Link, { type LinkProps } from "next/link";
import { type AnchorHTMLAttributes, createContext, type ReactNode, useContext, useMemo, useState } from "react";

type NavigationGuardValue = {
  blocked: boolean;
  setBlocked: (blocked: boolean) => void;
  confirmDiscard: () => boolean;
};

const NavigationGuardContext = createContext<NavigationGuardValue | null>(null);

export function NavigationGuardProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [blocked, setBlocked] = useState(false);
  const value = useMemo<NavigationGuardValue>(() => ({
    blocked,
    setBlocked,
    confirmDiscard: () => !blocked || window.confirm("You have unsaved changes. Discard them and leave this page?"),
  }), [blocked]);

  return <NavigationGuardContext.Provider value={value}>{children}</NavigationGuardContext.Provider>;
}

export function useNavigationGuard() {
  const value = useContext(NavigationGuardContext);
  if (!value) throw new Error("useNavigationGuard must be used within NavigationGuardProvider");
  return value;
}

type GuardedLinkProps = LinkProps & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps>;

export function GuardedLink({ onNavigate, ...props }: Readonly<GuardedLinkProps>) {
  const { confirmDiscard } = useNavigationGuard();
  return <Link {...props} onNavigate={(event) => {
    if (!confirmDiscard()) event.preventDefault();
    else onNavigate?.(event);
  }}/>;
}

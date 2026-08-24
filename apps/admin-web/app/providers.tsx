"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { AuthProvider } from "../components/auth-provider";

export function Providers({ children }: Readonly<{ children: ReactNode }>) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { retry: 1, staleTime: 15_000 } },
  }));
  return <QueryClientProvider client={client}><AuthProvider>{children}</AuthProvider></QueryClientProvider>;
}

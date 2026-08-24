"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";

import { api, ApiError, type User } from "../lib/api";

type AuthValue = { user: User | null; loading: boolean; login: (email: string, password: string) => Promise<User>; logout: () => Promise<void> };
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const queryClient = useQueryClient();
  const session = useQuery({
    queryKey: ["session"],
    queryFn: () => api<User>("/auth/me"),
    retry: false,
    throwOnError: false,
  });
  const user = session.error instanceof ApiError && session.error.status === 401 ? null : (session.data ?? null);
  async function login(email: string, password: string) {
    const current = await api<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    queryClient.setQueryData(["session"], current);
    return current;
  }
  async function logout() {
    if (user) await api<void>("/auth/logout", { method: "POST" }, user.csrf_token);
    queryClient.setQueryData(["session"], null);
    await queryClient.invalidateQueries();
  }
  return <AuthContext.Provider value={{ user, loading: session.isLoading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is missing");
  return value;
}

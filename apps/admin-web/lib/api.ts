export const API_URL = process.env.NEXT_PUBLIC_ARE_API_URL ?? "http://127.0.0.1:50003/api/v1";
export const PUBLIC_WEB_URL = process.env.NEXT_PUBLIC_ARE_PUBLIC_URL ?? "http://127.0.0.1:50001";

export type User = { id: string; email: string; display_name: string; roles: string[]; permissions: string[]; csrf_token: string };
export type PageResponse<T> = { items: T[]; meta: { page: number; page_size: number; total: number; pages: number } };
export type ResourceRecord = Record<string, unknown> & { id: string; slug?: string; status?: string; updated_at?: string };

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T>(path: string, init: RequestInit = {}, csrf?: string): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (csrf) headers.set("X-CSRF-Token", csrf);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers, credentials: "include" });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { error?: { message?: string }; detail?: { message?: string } } | null;
    throw new ApiError(response.status, body?.error?.message ?? body?.detail?.message ?? "The request could not be completed.");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

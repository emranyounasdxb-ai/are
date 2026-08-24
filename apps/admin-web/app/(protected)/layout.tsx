import type { ReactNode } from "react";
import { AdminShell } from "../../components/admin-shell";

export default function ProtectedLayout({ children }: Readonly<{ children: ReactNode }>) { return <AdminShell>{children}</AdminShell>; }

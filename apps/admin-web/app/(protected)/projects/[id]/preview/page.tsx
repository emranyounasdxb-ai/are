import { redirect } from "next/navigation";

import { PUBLIC_WEB_URL } from "../../../../../lib/api";

export default async function PreviewProjectPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = await params;
  redirect(`${PUBLIC_WEB_URL}/en/preview/projects/${encodeURIComponent(id)}`);
}

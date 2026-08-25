import type { Metadata } from "next";
import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { SiteFooter } from "../../../../../../components/navigation/site-footer";
import { ProjectDetailPresentation } from "../../../../../../components/projects/project-detail-presentation";
import { getDraftProjectPreview } from "../../../../../../lib/api";
import { homeCopy, isLocale } from "../../../../../../lib/home-copy";

type Props = Readonly<{ params: Promise<{ locale: string; projectId: string }> }>;

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Private Project preview | ALIYAS Real Estate",
  robots: { index: false, follow: false, nocache: true },
};

export default async function DraftProjectPreviewPage({ params }: Props) {
  const { locale, projectId } = await params;
  if (!isLocale(locale)) notFound();
  const requestHeaders = await headers();
  const project = await getDraftProjectPreview(
    locale,
    projectId,
    requestHeaders.get("cookie") ?? "",
  );
  if (!project) notFound();
  const mediaPrefix = `/${locale}/preview/projects/${encodeURIComponent(projectId)}/media`;
  const previewProject = {
    ...project,
    media: project.media?.map((item) => ({
      ...item,
      url: `${mediaPrefix}/${item.id}`,
    })),
  };

  return <div className="property-detail-page" id="top">
    <ProjectDetailPresentation locale={locale} preview project={previewProject}/>
    <SiteFooter copy={homeCopy[locale].header} locale={locale}/>
  </div>;
}

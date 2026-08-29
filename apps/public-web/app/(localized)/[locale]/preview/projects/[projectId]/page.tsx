import type { Metadata } from "next";
import { headers } from "next/headers";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SiteFooter } from "../../../../../../components/navigation/site-footer";
import { ProjectDetailPresentation } from "../../../../../../components/projects/project-detail-presentation";
import { getDraftProjectPreview } from "../../../../../../lib/api";
import { localizedBrand, localizedDisplayText, normalizeArabicUserFacingText } from "../../../../../../lib/arabic-localization";
import { homeCopy, isLocale } from "../../../../../../lib/home-copy";

type Props = Readonly<{ params: Promise<{ locale: string; projectId: string }> }>;

export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return {
    title: locale === "ar" ? `معاينة خاصة للمشروع | ${localizedBrand(locale)}` : "Private Project preview | ALIYAS Real Estate",
    robots: { index: false, follow: false, nocache: true },
  };
}

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
  const cover = previewProject.media?.find((item) => item.category === "cover");

  return <div className="property-detail-page" id="top">
    <ProjectDetailPresentation locale={locale} preview project={previewProject}/>
    <section className="inner-section" aria-labelledby="private-card-preview-title" id="private-card-preview">
      <h2 id="private-card-preview-title">{locale === "ar" ? "معاينة خاصة لبطاقة المشروع" : "Private Project card preview"}</h2>
      <p>{locale === "ar" ? "إذن عرض الغلاف لا يعني اعتماد المشروع أو نشره." : "Cover preview permission does not approve or publish this Project."}</p>
      <div className="cms-property-grid">
        <article>
          {cover ? <Image alt={locale === "ar" ? normalizeArabicUserFacingText(cover.alt ?? project.official_name) : cover.alt ?? ""} height={cover.height ?? 1080} width={cover.width ?? 1920}
            src={cover.url} unoptimized style={{ width: "100%", height: "auto", aspectRatio: "16 / 9", objectFit: "cover" }}/>
            : <div className="cms-media-neutral" aria-hidden="true">{locale === "ar" ? "علياس" : "ARE"}</div>}
          <div>
            <span>{project.emirate} · {locale === "ar" ? project.area.name_ar : project.area.name_en}</span>
            <h3>{localizedDisplayText(project.official_name, locale)}</h3>
            <p>{locale === "ar" ? normalizeArabicUserFacingText(project.short_summary) : project.short_summary}</p>
            <Link className="text-link" href={`/${locale}/preview/projects/${projectId}#top`}>
              {locale === "ar" ? "عرض المشروع" : "View project"}
            </Link>
          </div>
        </article>
      </div>
    </section>
    <SiteFooter copy={homeCopy[locale].header} locale={locale}/>
  </div>;
}

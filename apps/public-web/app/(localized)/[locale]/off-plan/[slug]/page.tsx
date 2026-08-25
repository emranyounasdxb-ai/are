import { notFound } from "next/navigation";

import { SiteFooter } from "../../../../../components/navigation/site-footer";
import { ProjectDetailPresentation } from "../../../../../components/projects/project-detail-presentation";
import { API_ORIGIN, getProject } from "../../../../../lib/api";
import { homeCopy, isLocale } from "../../../../../lib/home-copy";

type Props = Readonly<{ params: Promise<{ locale: string; slug: string }> }>;

export const dynamic = "force-dynamic";

export default async function ProjectDetailPage({ params }: Props) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const project = await getProject(locale, slug);
  if (!project) notFound();
  return <div className="property-detail-page" id="top">
    <ProjectDetailPresentation locale={locale} mediaBaseUrl={API_ORIGIN} project={project}/>
    <SiteFooter copy={homeCopy[locale].header} locale={locale}/>
  </div>;
}

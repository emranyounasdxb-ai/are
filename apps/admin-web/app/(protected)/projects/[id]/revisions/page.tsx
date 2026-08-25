import { ProjectRevisions } from "../../../../../components/project-revisions";

export default async function ProjectRevisionsPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = await params;
  return <ProjectRevisions projectId={id} />;
}

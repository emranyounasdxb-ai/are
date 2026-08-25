import { ProjectView } from "../../../../../components/project-view";

export default async function ViewProjectPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = await params;
  return <ProjectView id={id}/>;
}

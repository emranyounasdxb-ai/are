import { ProjectImportCandidateDetail } from "../../../../../../components/project-imports";

export default async function ProjectImportCandidatePage({ params }: Readonly<{ params: Promise<{ id: string; candidateId: string }> }>) {
  const { id, candidateId } = await params;
  return <ProjectImportCandidateDetail batchId={id} candidateId={candidateId}/>;
}

import { ProcessingJobDetail } from "../../../../components/project-processing";

export default async function ProcessingJobPage({
  params,
}: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = await params;
  return <ProcessingJobDetail id={id} />;
}

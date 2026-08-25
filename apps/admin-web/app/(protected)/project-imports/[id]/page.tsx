import { ProjectImportDetail } from "../../../../components/project-imports";

export default async function ProjectImportPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) { const { id } = await params; return <ProjectImportDetail id={id}/>; }

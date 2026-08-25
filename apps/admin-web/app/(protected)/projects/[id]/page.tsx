import { ProjectEditor } from "../../../../components/project-editor";

export default async function EditProjectPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) { const { id } = await params; return <ProjectEditor id={id}/>; }

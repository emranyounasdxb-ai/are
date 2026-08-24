import { DeveloperEditor } from "../../../../components/developer-editor";

export default async function EditDeveloperPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) { const { id } = await params; return <DeveloperEditor id={id}/>; }

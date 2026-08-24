import { ResourceEditor } from "../../../../../components/resource-editor";
export default async function EditJobPage({ params }: { params: Promise<{id:string}> }) { const { id } = await params; return <ResourceEditor id={id} kind="job"/>; }

import { ResourceEditor } from "../../../../components/resource-editor";
export default async function EditPropertyPage({ params }: { params: Promise<{id:string}> }) { const { id } = await params; return <ResourceEditor id={id} kind="property"/>; }

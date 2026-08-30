import { AreaEditor } from "../../../../components/area-editor";

export default async function EditAreaPage({ params }: Readonly<{ params: Promise<{ id: string }> }>) {
  const { id } = await params;
  return <AreaEditor id={id}/>;
}

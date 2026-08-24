import { SubmissionDetail } from "../../../../components/submission-detail";
export default async function Page({ params }: Readonly<{ params: Promise<{ id: string }> }>) { return <SubmissionDetail id={(await params).id} kind="enquiries"/>; }

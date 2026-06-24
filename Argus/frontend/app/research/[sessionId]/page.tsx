import { ResearchDashboard } from "@/components/ResearchDashboard";

export default async function ResearchSessionPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  return <ResearchDashboard initialSessionId={sessionId} />;
}

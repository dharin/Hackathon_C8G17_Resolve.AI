import { KnowledgeBaseSyncPanel } from "@/features/rag-configuration/knowledge-base-sync-panel";

export default function RagConfigurationPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 sm:p-6">
      <div>
        <h1 className="text-lg font-semibold">RAG Configuration</h1>
        <p className="text-sm text-muted-foreground">
          Sync the Remediation Agent&apos;s knowledge base from Confluence and
          the local SOP directory.
        </p>
      </div>
      <KnowledgeBaseSyncPanel />
    </div>
  );
}

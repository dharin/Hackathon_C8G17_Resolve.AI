import { SourceReferenceList } from "@/components/source-reference-list";
import type { Recommendation } from "@/types/incident";

export function RecommendationCard({
  recommendation,
}: {
  recommendation: Recommendation;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-sm font-semibold">{recommendation.title}</h4>
        <span className="shrink-0 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
          {Math.round(recommendation.confidence * 100)}% confidence
        </span>
      </div>
      <p className="mt-1.5 text-sm text-muted-foreground">
        {recommendation.reason}
      </p>
      <div className="mt-3">
        <p className="mb-1.5 text-xs font-medium text-muted-foreground">
          Supporting sources
        </p>
        <SourceReferenceList sources={recommendation.sources} />
      </div>
    </div>
  );
}

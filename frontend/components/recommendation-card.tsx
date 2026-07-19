import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SourceReferenceList } from "@/components/source-reference-list";
import type { Recommendation } from "@/types/analysis";

export function RecommendationCard({
  recommendation,
}: {
  recommendation: Recommendation;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{recommendation.title}</CardTitle>
        <CardDescription>{recommendation.rationale}</CardDescription>
        <CardAction>
          <Badge variant="secondary">
            {Math.round(recommendation.confidence * 100)}% confidence
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p className="mb-1.5 text-xs font-medium text-muted-foreground">
          Supporting sources
        </p>
        <SourceReferenceList sources={recommendation.sources} />
      </CardContent>
    </Card>
  );
}

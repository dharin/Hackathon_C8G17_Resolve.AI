import { FileText, FolderOpen, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatShortTimestamp } from "@/lib/format-date";
import type { SourceType } from "@/types/incident";
import type { RetrievedChunk } from "@/types/analysis";

const SOURCE_ICON: Record<SourceType, typeof FileText> = {
  confluence: FileText,
  local_sop: FolderOpen,
};

const SOURCE_LABEL: Record<SourceType, string> = {
  confluence: "Confluence",
  local_sop: "Local SOP",
};

export function SourceReferenceList({
  sources,
}: {
  sources: RetrievedChunk[];
}) {
  if (sources.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        No supporting documentation found.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {sources.map((source) => {
        const Icon = SOURCE_ICON[source.source_type];
        return (
          <li
            key={source.chunk_id}
            className="flex items-start gap-2.5 rounded-xl border border-border bg-background px-3 py-2"
          >
            <Icon className="mt-0.5 size-4 shrink-0 text-primary" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">
                  {source.title}
                </span>
                <Badge variant="secondary">
                  {SOURCE_LABEL[source.source_type]}
                </Badge>
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {source.section_path.length > 0
                  ? source.section_path.join(" › ")
                  : "Untitled section"}{" "}
                · Updated{" "}
                {source.updated_at
                  ? formatShortTimestamp(source.updated_at)
                  : "unknown"}
              </p>
              {source.source_type === "local_sop" && (
                <p className="mt-0.5 truncate font-mono text-xs text-muted-foreground/80">
                  {source.source_uri}
                </p>
              )}
            </div>
            {source.source_type === "confluence" && (
              <Button
                variant="ghost"
                size="icon-xs"
                aria-label={`Open ${source.title}`}
                nativeButton={false}
                render={
                  <a
                    href={source.source_uri}
                    target="_blank"
                    rel="noopener noreferrer"
                  />
                }
              >
                <ExternalLink />
              </Button>
            )}
          </li>
        );
      })}
    </ul>
  );
}

import { FileText, HardDrive, History, ExternalLink } from "lucide-react";
import type { SourceReference, SourceType } from "@/types/incident";

const SOURCE_ICON: Record<SourceType, typeof FileText> = {
  confluence: FileText,
  "google-drive": HardDrive,
  "historical-incident": History,
};

const SOURCE_LABEL: Record<SourceType, string> = {
  confluence: "Confluence",
  "google-drive": "Google Drive",
  "historical-incident": "Historical Incident",
};

export function SourceReferenceList({
  sources,
}: {
  sources: SourceReference[];
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
        const Icon = SOURCE_ICON[source.type];
        return (
          <li
            key={source.id}
            className="flex items-start gap-2.5 rounded-xl border border-border bg-background px-3 py-2"
          >
            <Icon className="mt-0.5 size-4 shrink-0 text-primary" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">
                  {source.title}
                </span>
                <span className="shrink-0 rounded-full bg-accent px-2 py-0.5 text-[10px] font-medium text-accent-foreground">
                  {SOURCE_LABEL[source.type]}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {source.section} · Updated {source.lastUpdated}
              </p>
            </div>
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open ${source.title}`}
              className="shrink-0 rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <ExternalLink className="size-3.5" />
            </a>
          </li>
        );
      })}
    </ul>
  );
}

"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import { openLocalSopDocument } from "@/services/rag-service";
import type { RetrievedChunk } from "@/types/analysis";

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
    <ul className="flex flex-col gap-1">
      {sources.map((source) => (
        <li key={source.chunk_id}>
          <SourceLink source={source} />
        </li>
      ))}
    </ul>
  );
}

const LINK_CLASSNAME =
  "text-left text-sm font-medium text-primary underline-offset-2 hover:underline disabled:cursor-not-allowed disabled:opacity-60";

function SourceLink({ source }: { source: RetrievedChunk }) {
  const { getToken } = useAuth();
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (source.source_type === "confluence") {
    return (
      <a
        href={source.source_uri}
        target="_blank"
        rel="noopener noreferrer"
        className={LINK_CLASSNAME}
      >
        {source.title}
      </a>
    );
  }

  return (
    <div className="flex flex-col gap-0.5">
      <button
        type="button"
        disabled={opening}
        onClick={async () => {
          // Must be the first synchronous statement in this handler — see
          // openLocalSopDocument's doc comment.
          const newTab = window.open("", "_blank");
          setError(null);
          setOpening(true);
          try {
            const token = await getToken();
            await openLocalSopDocument(source.source_uri, token, newTab);
          } catch {
            setError("Couldn't open this document.");
          } finally {
            setOpening(false);
          }
        }}
        className={cn(LINK_CLASSNAME)}
      >
        {source.title}
      </button>
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  );
}

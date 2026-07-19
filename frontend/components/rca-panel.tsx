import type { RCAReport } from "@/types/incident";

function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-xs font-medium text-muted-foreground">
        {Math.round(value * 100)}%
      </span>
    </div>
  );
}

export function RcaPanel({ rca }: { rca: RCAReport | null }) {
  if (!rca) {
    return (
      <div className="rounded-2xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
        RCA has not been generated for this incident yet.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <section className="rounded-2xl border border-border bg-card p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Primary Cause</h3>
          <ConfidenceMeter value={rca.confidence} />
        </div>
        <p className="text-sm text-foreground/90">{rca.primaryCause}</p>
      </section>

      <section className="rounded-2xl border border-border bg-card p-4">
        <h3 className="mb-2 text-sm font-semibold">Evidence</h3>
        <ul className="flex flex-col gap-1.5">
          {rca.evidence.map((item) => (
            <li
              key={item}
              className="rounded-lg bg-muted px-3 py-2 font-mono text-xs text-foreground/80"
            >
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-border bg-card p-4">
        <h3 className="mb-2 text-sm font-semibold">Alternative Causes</h3>
        {rca.alternativeCauses.length === 0 ? (
          <p className="text-sm text-muted-foreground">None identified.</p>
        ) : (
          <ul className="flex flex-col gap-1.5 text-sm text-foreground/80">
            {rca.alternativeCauses.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-muted-foreground">–</span>
                {item}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

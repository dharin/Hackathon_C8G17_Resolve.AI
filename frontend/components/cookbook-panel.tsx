import type { Cookbook } from "@/types/incident";

function StepList({ items }: { items: string[] }) {
  return (
    <ol className="flex flex-col gap-1.5">
      {items.map((item, index) => (
        <li key={item} className="flex gap-2.5 text-sm text-foreground/90">
          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium text-muted-foreground">
            {index + 1}
          </span>
          {item}
        </li>
      ))}
    </ol>
  );
}

export function CookbookPanel({ cookbook }: { cookbook: Cookbook | null }) {
  if (!cookbook) {
    return (
      <div className="rounded-2xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
        No runbook generated for this incident yet.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <section className="rounded-2xl border border-border bg-card p-4">
        <h3 className="mb-2 text-sm font-semibold">Root Cause</h3>
        <p className="text-sm text-foreground/90">{cookbook.rootCause}</p>
      </section>

      <section className="rounded-2xl border border-border bg-card p-4">
        <h3 className="mb-2 text-sm font-semibold">Recommended Steps</h3>
        <StepList items={cookbook.steps} />
      </section>

      <section className="rounded-2xl border border-border bg-card p-4">
        <h3 className="mb-2 text-sm font-semibold">Executable Commands</h3>
        <div className="flex flex-col gap-1.5">
          {cookbook.commands.map((command) => (
            <pre
              key={command}
              className="overflow-x-auto rounded-lg bg-muted px-3 py-2 font-mono text-xs text-foreground/80"
            >
              {command}
            </pre>
          ))}
        </div>
      </section>

      <div className="grid gap-5 sm:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h3 className="mb-2 text-sm font-semibold">Validation</h3>
          <StepList items={cookbook.validation} />
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h3 className="mb-2 text-sm font-semibold">Rollback</h3>
          <StepList items={cookbook.rollback} />
        </section>
      </div>
    </div>
  );
}

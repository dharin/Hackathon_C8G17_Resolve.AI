"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  RotateCcw,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from "@/components/ui/progress";
import {
  formatBytes,
  hasAllowedExtension,
  MAX_UPLOAD_SIZE_BYTES,
  ALLOWED_LOG_EXTENSIONS,
} from "@/lib/upload-config";
import { uploadLogFile, UploadError } from "@/services/upload-service";
import { analyzeLog, AnalysisError } from "@/services/analysis-service";
import type { LogUploadResult } from "@/types/upload";

type UploadState =
  | { status: "idle" }
  | { status: "uploading"; file: File; progress: number; abort: () => void }
  | { status: "analyzing"; file: File; result: LogUploadResult }
  | { status: "success"; file: File; result: LogUploadResult }
  | { status: "error"; file: File | null; message: string };

function validateFile(file: File): string | null {
  if (!hasAllowedExtension(file.name)) {
    return `Unsupported file type. Allowed types: ${ALLOWED_LOG_EXTENSIONS.join(", ")}.`;
  }
  if (file.size === 0) {
    return "File is empty.";
  }
  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return `File exceeds the ${formatBytes(MAX_UPLOAD_SIZE_BYTES)} upload limit.`;
  }
  return null;
}

export function UploadPanel() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const locked = state.status === "uploading" || state.status === "analyzing";

  const startUpload = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setState({ status: "error", file: null, message: validationError });
        return;
      }

      const token = await getToken();
      const { promise, abort } = uploadLogFile(file, token, (progress) => {
        setState((prev) =>
          prev.status === "uploading" ? { ...prev, progress } : prev,
        );
      });

      setState({ status: "uploading", file, progress: 0, abort });

      let result: LogUploadResult;
      try {
        result = await promise;
      } catch (err) {
        const message =
          err instanceof UploadError ? err.message : "Upload failed.";
        setState({ status: "error", file, message });
        return;
      }

      // Immediately run the Log Reader Agent against the uploaded file so
      // the user lands straight on their incidents — mirrors the Upload ->
      // Incidents step of the LangGraph pipeline (see backend/graph/).
      setState({ status: "analyzing", file, result });
      try {
        const analysisToken = await getToken();
        const analysis = await analyzeLog(result.upload_id, analysisToken);
        router.push(`/?analysis=${analysis.analysis_id}`);
        setState({ status: "success", file, result });
      } catch (err) {
        const message =
          err instanceof AnalysisError ? err.message : "Analysis failed.";
        setState({ status: "error", file, message });
      }
    },
    [getToken, router],
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (locked || !files || files.length === 0) return;
      startUpload(files[0]);
    },
    [locked, startUpload],
  );

  const reset = useCallback(() => {
    setState({ status: "idle" });
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      <div
        role="button"
        tabIndex={locked ? -1 : 0}
        aria-disabled={locked}
        onClick={() => !locked && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (!locked && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!locked) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-colors",
          locked
            ? "cursor-not-allowed border-border bg-muted/50 opacity-60"
            : "cursor-pointer border-border bg-card hover:border-primary/50 hover:bg-accent/30",
          isDragging && !locked && "border-primary bg-accent/50",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_LOG_EXTENSIONS.join(",")}
          disabled={locked}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <UploadCloud className="size-6" />
        </div>
        <div>
          <p className="text-sm font-medium">
            Drag and drop a log file, or click to browse
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {ALLOWED_LOG_EXTENSIONS.join(" / ")} · up to{" "}
            {formatBytes(MAX_UPLOAD_SIZE_BYTES)}
          </p>
        </div>
      </div>

      {state.status === "uploading" && (
        <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2 text-sm">
              <FileText className="size-4 shrink-0 text-muted-foreground" />
              <span className="truncate font-medium">{state.file.name}</span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {formatBytes(state.file.size)}
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Cancel upload"
              onClick={() => {
                state.abort();
                reset();
              }}
            >
              <X />
            </Button>
          </div>
          <Progress value={state.progress}>
            <ProgressLabel className="text-xs text-muted-foreground">
              Uploading…
            </ProgressLabel>
            <ProgressValue className="text-xs" />
          </Progress>
        </div>
      )}

      {state.status === "analyzing" && (
        <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
          <div className="flex min-w-0 items-center gap-2 text-sm">
            <Loader2 className="size-4 shrink-0 animate-spin text-primary" />
            <span className="truncate font-medium">{state.file.name}</span>
            <span className="shrink-0 text-xs text-muted-foreground">
              Detecting incidents…
            </span>
          </div>
        </div>
      )}

      {state.status === "success" && (
        <div className="flex flex-col gap-3">
          <Alert>
            <CheckCircle2 className="text-primary" />
            <AlertTitle>Analysis complete</AlertTitle>
            <AlertDescription>
              <span className="truncate">
                {state.result.file_name} ·{" "}
                {formatBytes(state.result.size_bytes)}
              </span>
              <span className="font-mono">
                upload_id: {state.result.upload_id}
              </span>
            </AlertDescription>
          </Alert>
          <Button variant="outline" className="w-fit" onClick={reset}>
            <RotateCcw data-icon="inline-start" />
            Upload another file
          </Button>
        </div>
      )}

      {state.status === "error" && (
        <div className="flex flex-col gap-3">
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>Upload failed</AlertTitle>
            <AlertDescription>
              {state.file && (
                <span className="truncate">
                  {state.file.name} · {formatBytes(state.file.size)}
                </span>
              )}
              <span>{state.message}</span>
            </AlertDescription>
          </Alert>
          <Button variant="outline" className="w-fit" onClick={reset}>
            <RotateCcw data-icon="inline-start" />
            Try again
          </Button>
        </div>
      )}
    </div>
  );
}

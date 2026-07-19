import { UploadPanel } from "@/features/upload/upload-panel";

export default function UploadLogsPage() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 sm:p-6">
      <div>
        <h1 className="text-lg font-semibold">Upload Logs</h1>
        <p className="text-sm text-muted-foreground">
          Upload an application log file to start incident analysis.
        </p>
      </div>
      <UploadPanel />
    </div>
  );
}

import { API_BASE_URL } from "@/lib/upload-config";
import type { LogUploadResult } from "@/types/upload";

export class UploadError extends Error {}

export function uploadLogFile(
  file: File,
  token: string | null,
  onProgress: (percent: number) => void,
): { promise: Promise<LogUploadResult>; abort: () => void } {
  const xhr = new XMLHttpRequest();

  const promise = new Promise<LogUploadResult>((resolve, reject) => {
    xhr.open("POST", `${API_BASE_URL}/api/v1/logs/upload`);
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // non-JSON response, fall through to status-based error below
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as LogUploadResult);
        return;
      }

      const detail =
        body && typeof body === "object" && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : `Upload failed with status ${xhr.status}.`;
      reject(new UploadError(detail));
    };

    xhr.onerror = () =>
      reject(
        new UploadError(
          "Network error while uploading. Is the backend running?",
        ),
      );
    xhr.onabort = () => reject(new UploadError("Upload cancelled."));

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });

  return { promise, abort: () => xhr.abort() };
}

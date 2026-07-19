export const ALLOWED_LOG_EXTENSIONS = [".log", ".txt"] as const;

export const MAX_UPLOAD_SIZE_BYTES =
  Number(process.env.NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB ?? 10) * 1024 * 1024;

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function hasAllowedExtension(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return ALLOWED_LOG_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

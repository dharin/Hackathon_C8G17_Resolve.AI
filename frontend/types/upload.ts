export interface LogUploadResult {
  upload_id: string;
  file_name: string;
  size_bytes: number;
  status: "uploaded";
}

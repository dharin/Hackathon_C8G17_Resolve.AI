import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from config.settings import ALLOWED_LOG_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR
from models.log_upload import LogUploadResult

CHUNK_SIZE = 1024 * 1024  # 1 MB


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation. Carries an HTTP status code."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _validate_extension(file_name: str) -> str:
    if not file_name:
        raise UploadValidationError(400, "File name is missing.")

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_LOG_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_LOG_EXTENSIONS))
        raise UploadValidationError(
            415, f"Unsupported file type '{ext or '(none)'}'. Allowed types: {allowed}."
        )
    return ext


async def save_log_upload(upload: UploadFile) -> LogUploadResult:
    """Validates and persists an uploaded log file. Never parses or executes its contents."""

    ext = _validate_extension(upload.filename or "")

    upload_id = uuid.uuid4().hex
    # Stored path is built entirely from server-generated values (uuid + an
    # extension drawn from an allowlist) — the original file name is never
    # used to build a path, so there's no path-traversal surface here.
    dest_path = UPLOAD_DIR / f"{upload_id}{ext}"

    size_bytes = 0
    try:
        with dest_path.open("wb") as dest:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise UploadValidationError(
                        413,
                        f"File exceeds the {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB upload limit.",
                    )
                dest.write(chunk)
    except UploadValidationError:
        dest_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    if size_bytes == 0:
        dest_path.unlink(missing_ok=True)
        raise UploadValidationError(400, "Uploaded file is empty.")

    return LogUploadResult(
        upload_id=upload_id,
        file_name=os.path.basename(upload.filename),
        size_bytes=size_bytes,
        status="uploaded",
    )

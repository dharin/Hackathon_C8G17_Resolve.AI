from typing import Literal

from pydantic import BaseModel


class LogUploadResult(BaseModel):
    upload_id: str
    file_name: str
    size_bytes: int
    status: Literal["uploaded"]

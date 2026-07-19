from fastapi import APIRouter, Depends, HTTPException, UploadFile

from api.deps import get_current_user
from models.log_upload import LogUploadResult
from models.user import UserIdentity
from services.upload_service import UploadValidationError, save_log_upload

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.post("/upload", response_model=LogUploadResult)
async def upload_log(
    file: UploadFile,
    _user: UserIdentity = Depends(get_current_user),
) -> LogUploadResult:
    try:
        return await save_log_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

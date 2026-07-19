from fastapi import APIRouter, Depends

from api.deps import get_current_user
from models.user import UserIdentity

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get("/me", response_model=UserIdentity)
def read_current_user(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
    return user

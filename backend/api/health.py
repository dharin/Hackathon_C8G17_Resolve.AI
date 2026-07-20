from fastapi import APIRouter, Depends

from api.deps import get_current_user
from models.health import HealthCheckResult
from models.user import UserIdentity
from services import health_service

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health/integrations", response_model=HealthCheckResult)
def get_integration_health(_user: UserIdentity = Depends(get_current_user)) -> HealthCheckResult:
    return health_service.check_all()

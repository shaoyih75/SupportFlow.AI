from fastapi import APIRouter, Depends

from app.deps import get_user_service
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.user_service import UserService

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, service: UserService = Depends(get_user_service)):
    return service.register(payload)

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.security import create_access_token
from app.deps import get_current_user, get_user_service
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, service: UserService = Depends(get_user_service)):
    return service.register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: UserService = Depends(get_user_service)):
    """JSON login used by the frontend."""
    user = service.authenticate(payload.email, payload.password)
    return TokenResponse(access_token=create_access_token(subject=str(user.id)))


@router.post("/token", response_model=TokenResponse, include_in_schema=True)
def login_form(form: OAuth2PasswordRequestForm = Depends(), service: UserService = Depends(get_user_service)):
    """Form login for Swagger's "Authorize" button (OAuth2 password flow: `username` = email)."""
    user = service.authenticate(form.username, form.password)
    return TokenResponse(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt only uses the first 72 bytes


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    # Tells the client how to send it: `Authorization: Bearer <access_token>`.
    token_type: str = "bearer"


class UserResponse(BaseModel):
    # No password_hash here: the ORM User has it, the API contract does not.
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    created_at: datetime


class RegisterResponse(BaseModel):
    user: UserResponse
    personal_workspace_id: UUID

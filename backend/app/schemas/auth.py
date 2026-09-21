import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: uuid.UUID
    email: str
    full_name: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    uid: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: Optional[str] = None
    role: RoleResponse
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    phone: Optional[str] = None
    role_name: str

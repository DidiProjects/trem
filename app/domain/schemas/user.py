from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
import re


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    profile_name: str  # 'file_editor' | 'airline_company'

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username deve ter entre 3 e 50 caracteres")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username só pode conter letras, números, _, . e -")
        return v

    @field_validator("email")
    @classmethod
    def email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Email inválido")
        return v

    @field_validator("profile_name")
    @classmethod
    def valid_profile(cls, v: str) -> str:
        allowed = {"file_editor", "airline_company"}
        if v not in allowed:
            raise ValueError(f"Perfil deve ser um de: {', '.join(allowed)}")
        return v


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    profile_name: str
    status: str
    must_change_password: bool
    provisional_password_sent_at: Optional[datetime]
    created_at: datetime
    last_login_at: Optional[datetime]

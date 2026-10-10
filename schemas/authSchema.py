
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    ADMIN = "Admin"
    ORGANIZER = "Organizer"
    ATTENDEE = "Attendee"


class RegisterUsers(BaseModel):
    user_name: str = Field(
        min_length=2,
        max_length=50,
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
    )

    @field_validator("user_name")
    @classmethod
    def validate_user_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters")

        if not value:
            raise ValueError("Name cannot be empty")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")

        if not value.strip():
            raise ValueError("Password cannot be empty or whitespace only")

        return value


class LoginUsers(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

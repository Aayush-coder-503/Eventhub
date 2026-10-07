from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "Admin"
    ORGANIZER = "Organizer"
    ATTENDEE = "Attendee"

class RegisterUsers(BaseModel):
    user_name: str
    email: str
    password: str
    role: UserRole


class LoginUsers(BaseModel):
    email:str
    password: str

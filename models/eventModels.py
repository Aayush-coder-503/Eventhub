from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    CANCELLED = "Cancelled"

class CreateEvent(BaseModel):
    title: str
    description: str
    venue: str
    start_time: datetime
    end_time: datetime
    capacity: int
    price: float
    status: Status



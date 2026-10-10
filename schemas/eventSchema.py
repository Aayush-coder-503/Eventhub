from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


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
    capacity: int = Field(gt=0)
    price: float = Field(gt=0)
    status: Status
    category_id: uuid.UUID



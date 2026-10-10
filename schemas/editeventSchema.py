from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import uuid


class EditStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    CANCELLED = "Cancelled"

class EditEvent(BaseModel):
    title: str | None = None
    description: str | None = None
    venue: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = None
    price: float | None = None
    status: EditStatus | None = None
    category_id: uuid.UUID | None = None
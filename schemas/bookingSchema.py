from pydantic import BaseModel, Field
from enum import Enum

#confirmed / cancelled

class BookingStatus(str, Enum):
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"


class Book(BaseModel):
    seats: int = Field(gt=0)

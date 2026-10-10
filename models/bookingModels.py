from db.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum, Integer, CheckConstraint, UniqueConstraint
from datetime import datetime
from enum import Enum
from schemas.bookingSchema import BookingStatus

class Booking(Base):
    __tablename__ = "booking"

    __table_args__ = (
        CheckConstraint("seats > 0", name="check_booking_seats_positive"),
        UniqueConstraint("user_id", "event_id", name="uq_booking_user_event"),
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.user_id"),
        nullable=False
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("event.event_id"),
        nullable=False
    )

    seats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus),
        nullable=False,
        default=BookingStatus.CONFIRMED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )




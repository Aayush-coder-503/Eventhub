import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from db.db import Base
from models.categoryModels import Categories

class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[uuid:UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    category_names: Mapped[Categories] = mapped_column(
        SQLEnum(Categories),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )


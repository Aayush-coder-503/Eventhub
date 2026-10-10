
import uuid

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.eventModels import Event
from models.categoryModels import Category
from models.bookingModels import Booking

from schemas.authSchema import UserRole
from schemas.eventSchema import CreateEvent, Status
from schemas.editeventSchema import EditEvent
from schemas.bookingSchema import BookingStatus

from core.security.dependencies import get_authenticated_user

import math
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.eventModels import Event


async def get_events(
    db: AsyncSession,
    page: int = 1,
    size: int = 10,
    category_id: uuid.UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    sort_by: str = "date",
    order: str = "asc",
):
    # Validate ranges
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be before or equal to end_date",
        )

    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise HTTPException(
                status_code=422,
                detail="min_price cannot exceed max_price",
            )

    # Start with non-deleted events
    query = select(Event).where(
        Event.is_deleted.is_(False),
        Event.status == Status.PUBLISHED,
    )

    # Apply optional filters
    if category_id is not None:
        query = query.where(Event.category_id == category_id)

    if start_date is not None:
        query = query.where(Event.start_time >= start_date)

    if end_date is not None:
        query = query.where(Event.start_time <= end_date)

    if min_price is not None:
        query = query.where(Event.price >= min_price)

    if max_price is not None:
        query = query.where(Event.price <= max_price)

    if search and search.strip():
        query = query.where(
            Event.title.ilike(f"%{search.strip()}%")
        )

    # Count the matching events BEFORE pagination
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Choose the sorting column
    sort_columns = {
        "date": Event.start_time,
        "price": Event.price,
    }

    sort_column = sort_columns[sort_by]
    sort_expression = (
        asc(sort_column) if order == "asc"
        else desc(sort_column)
    )

    # event_id provides consistent ordering when values are equal
    query = query.order_by(
        sort_expression,
        asc(Event.event_id),
    )

    # Pagination: page 1 skips 0 rows, page 2 skips `size` rows
    offset = (page - 1) * size

    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    events = result.scalars().all()

    # Return explicit response data
    event_list = [
        {
            "event_id": str(event.event_id),
            "title": event.title,
            "description": event.description,
            "venue": event.venue,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "capacity": event.capacity,
            "price": float(event.price),
            "category_id": str(event.category_id),
            "organizer_id": str(event.organizer_id),
            "status": event.status.value,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }
        for event in events
    ]

    return {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": math.ceil(total / size) if total else 0,
        "events": event_list,
    }


async def create_event(
    event: CreateEvent,
    authorization: str,
    db: AsyncSession,
):
    user = await get_authenticated_user(authorization, db)

    if user.role != UserRole.ORGANIZER:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create events",
        )

    category_result = await db.execute(
        select(Category).where(
            Category.category_id == event.category_id
        )
    )
    category = category_result.scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category doesn't exist",
        )

    new_event = Event(
        event_id=uuid.uuid4(),
        title=event.title,
        description=event.description,
        venue=event.venue,
        start_time=event.start_time,
        end_time=event.end_time,
        capacity=event.capacity,
        price=event.price,
        organizer_id=user.user_id,
        category_id=event.category_id,
        status=event.status,
    )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    return {
        "event": {
            "title": new_event.title,
            "description": new_event.description,
            "venue": new_event.venue,
            "start_time": new_event.start_time,
            "end_time": new_event.end_time,
            "capacity": new_event.capacity,
            "price": new_event.price,
            "status": new_event.status.value,
            "category": category.category_names,
        }
    }


async def edit_event(
    event_id: uuid.UUID,
    edit_event: EditEvent,
    authorization: str,
    db: AsyncSession,
):
    async with db.begin():
        user = await get_authenticated_user(authorization, db)

        if user.role != UserRole.ORGANIZER:
            raise HTTPException(
                status_code=403,
                detail="Only organizers can edit events",
            )

        result = await db.execute(
            select(Event)
            .where(Event.event_id == event_id)
            .with_for_update()
        )
        existing_event = result.scalar_one_or_none()

        if existing_event is None:
            raise HTTPException(
                status_code=404,
                detail="Event doesn't exist",
            )

        if existing_event.organizer_id != user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only edit your own events",
            )

        update_data = edit_event.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided to update",
            )

        if "capacity" in update_data:
            booking_result = await db.execute(
                select(
                    func.coalesce(func.sum(Booking.seats), 0)
                ).where(
                    Booking.event_id == event_id,
                    Booking.status == BookingStatus.CONFIRMED,
                )
            )
            booked_seats = booking_result.scalar_one()

            if update_data["capacity"] < booked_seats:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Capacity cannot be lower than "
                        f"{booked_seats} confirmed seats already booked"
                    ),
                )

        if "category_id" in update_data:
            category_result = await db.execute(
                select(Category).where(
                    Category.category_id == update_data["category_id"]
                )
            )
            category = category_result.scalar_one_or_none()

            if category is None:
                raise HTTPException(
                    status_code=404,
                    detail="Category doesn't exist",
                )

        for field, value in update_data.items():
            setattr(existing_event, field, value)

        response = {
            "message": "Event updated successfully",
            "event": {
                "event_id": str(existing_event.event_id),
                "title": existing_event.title,
                "description": existing_event.description,
                "venue": existing_event.venue,
                "start_time": existing_event.start_time,
                "end_time": existing_event.end_time,
                "capacity": existing_event.capacity,
                "price": existing_event.price,
                "status": existing_event.status.value,
                "category_id": str(existing_event.category_id),
            },
        }

    return response


async def delete_event(
    event_id: uuid.UUID,
    authorization: str,
    db: AsyncSession,
):
    async with db.begin():
        user = await get_authenticated_user(authorization, db)

        if user.role != UserRole.ORGANIZER:
            raise HTTPException(
                status_code=403,
                detail="Only organizers can delete events",
            )

        result = await db.execute(
            select(Event)
            .where(Event.event_id == event_id)
            .with_for_update()
        )
        existing_event = result.scalar_one_or_none()

        if existing_event is None or existing_event.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="Event doesn't exist",
            )

        if existing_event.organizer_id != user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own events",
            )

        existing_event.is_deleted = True

    return {"message": "Deleted event successfully"}

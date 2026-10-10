from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid

from db.db import get_db
from models.userModels import User
from models.eventModels import Event
from models.bookingModels import Booking
from schemas.authSchema import UserRole
from schemas.bookingSchema import BookingStatus
from routers.eventRoutes import get_authenticated_user

router = APIRouter()


@router.get("/profile")
async def profile(
    authorization: str = Header(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_authenticated_user(
        authorization=authorization,
        db=db,
    )

    profile_data = {
        "user_id": str(user.user_id),
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
    }

    # ADMIN PROFILE
    if user.role == UserRole.ADMIN:
        return {
            "message": "Profile fetched successfully",
            "profile": profile_data,
        }

    # ORGANIZER PROFILE + THEIR EVENTS
    elif user.role == UserRole.ORGANIZER:
        result = await db.execute(
            select(Event)
            .where(
                Event.organizer_id == user.user_id,
                Event.is_deleted == False,
            )
        )
        events = result.scalars().all()

        profile_data["organized_events"] = [
            {
                "event_id": str(event.event_id),
                "title": event.title,
                "description": event.description,
                "venue": event.venue,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "capacity": event.capacity,
                "price": event.price,
                "status": event.status.value,
                "category_id": str(event.category_id),
            }
            for event in events
        ]

        return {
            "message": "Profile fetched successfully",
            "profile": profile_data,
        }

    # ATTENDEE PROFILE + THEIR BOOKINGS
    elif user.role == UserRole.ATTENDEE:
        result = await db.execute(
            select(Booking, Event)
            .join(Event, Booking.event_id == Event.event_id)
            .where(Booking.user_id == user.user_id)
        )
        bookings = result.all()

        profile_data["bookings"] = [
            {
                "booking_id": str(booking.booking_id),
                "booking_status": booking.status.value,
                "seats": booking.seats,
                "event": {
                    "event_id": str(event.event_id),
                    "title": event.title,
                    "description": event.description,
                    "venue": event.venue,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "price": event.price,
                    "status": event.status.value,
                },
            }
            for booking, event in bookings
        ]

        return {
            "message": "Profile fetched successfully",
            "profile": profile_data,
        }

    else:
        raise HTTPException(
            status_code=403,
            detail="Invalid user role",
        )
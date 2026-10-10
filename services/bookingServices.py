
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.userModels import User
from models.eventModels import Event
from models.bookingModels import Booking
from schemas.authSchema import UserRole
from schemas.eventSchema import Status
from schemas.bookingSchema import Book, BookingStatus

from services.profileServices import get_user_profile


async def book_seat(
    event_id: uuid.UUID,
    book: Book,
    authorization: str,
    db: AsyncSession,
):
    try:
        async with db.begin():
            user = await get_authenticated_user(
                authorization=authorization,
                db=db,
            )

            if user.role != UserRole.ATTENDEE:
                raise HTTPException(
                    status_code=403,
                    detail="You are not allowed to book events",
                )

            event_result = await db.execute(
                select(Event)
                .where(Event.event_id == event_id)
                .with_for_update()
            )
            event = event_result.scalar_one_or_none()

            if event is None or event.is_deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Event doesn't exist",
                )

            if event.status == Status.CANCELLED:
                raise HTTPException(
                    status_code=400,
                    detail="This event has been cancelled",
                )

            if event.status != Status.PUBLISHED:
                raise HTTPException(
                    status_code=400,
                    detail="This event is not published",
                )

            if event.start_time <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot book an event that has already started",
                )

            booking_check = await db.execute(
                select(Booking).where(
                    Booking.user_id == user.user_id,
                    Booking.event_id == event_id,
                )
            )
            existing_booking = booking_check.scalar_one_or_none()

            if existing_booking is not None:
                raise HTTPException(
                    status_code=409,
                    detail="You have already booked this event",
                )

            booking_result = await db.execute(
                select(
                    func.coalesce(func.sum(Booking.seats), 0)
                ).where(
                    Booking.event_id == event_id,
                    Booking.status == BookingStatus.CONFIRMED,
                )
            )
            booked_seats = booking_result.scalar_one()
            available_seats = event.capacity - booked_seats

            if book.seats > available_seats:
                raise HTTPException(
                    status_code=409,
                    detail=f"Only {available_seats} seats are available",
                )

            new_booking = Booking(
                user_id=user.user_id,
                event_id=event_id,
                seats=book.seats,
                status=BookingStatus.CONFIRMED,
            )

            db.add(new_booking)
            await db.flush()

            response = {
                "message": "Booking created successfully",
                "booking_id": str(new_booking.booking_id),
                "event_id": str(new_booking.event_id),
                "seats": new_booking.seats,
                "status": new_booking.status.value,
            }

        return response

    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Booking conflicts with an existing database constraint",
        ) from exc


async def cancel_booking(
    booking_id: uuid.UUID,
    authorization: str,
    db: AsyncSession,
):
    async with db.begin():
        user = await get_authenticated_user(
            authorization=authorization,
            db=db,
        )

        result = await db.execute(
            select(Booking)
            .where(Booking.booking_id == booking_id)
            .with_for_update()
        )
        booking = result.scalar_one_or_none()

        if booking is None:
            raise HTTPException(
                status_code=404,
                detail="Booking doesn't exist",
            )

        if booking.user_id != user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only cancel your own bookings",
            )

        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=409,
                detail="Booking is already cancelled",
            )

        booking.status = BookingStatus.CANCELLED

        response = {
            "message": "Booking cancelled successfully",
            "booking_id": str(booking.booking_id),
            "event_id": str(booking.event_id),
            "status": booking.status.value,
        }

    return response


async def get_booked_seats(
    event_id: uuid.UUID,
    authorization: str,
    db: AsyncSession,
):
    user = await get_authenticated_user(
        authorization=authorization,
        db=db,
    )

    if user.role not in [UserRole.ADMIN, UserRole.ORGANIZER]:
        raise HTTPException(
            status_code=403,
            detail="Only admins and organizers can view booked seats",
        )

    event_result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    event = event_result.scalar_one_or_none()

    if event is None or event.is_deleted:
        raise HTTPException(
            status_code=404,
            detail="Event doesn't exist",
        )

    if (
        user.role == UserRole.ORGANIZER
        and event.organizer_id != user.user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only view bookings for your own events",
        )

    result = await db.execute(
        select(Booking, User)
        .join(User, Booking.user_id == User.user_id)
        .where(
            Booking.event_id == event_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    bookings = result.all()

    total_booked_seats = sum(
        booking.seats for booking, attendee in bookings
    )

    return {
        "message": "Booked seats fetched successfully",
        "event": {
            "event_id": str(event.event_id),
            "title": event.title,
            "capacity": event.capacity,
            "total_booked_seats": total_booked_seats,
            "available_seats": event.capacity - total_booked_seats,
        },
        "bookings": [
            {
                "booking_id": str(booking.booking_id),
                "attendee": {
                    "user_id": str(attendee.user_id),
                    "name": attendee.name,
                    "email": attendee.email,
                },
                "seats_booked": booking.seats,
                "status": booking.status.value,
            }
            for booking, attendee in bookings
        ],
    }

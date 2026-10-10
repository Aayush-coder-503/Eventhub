from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timezone


from db.db import get_db

from models.userModels import User
from schemas.authSchema import UserRole

from models.eventModels import Event
from schemas.eventSchema import CreateEvent, Status

from models.bookingModels import Booking
from schemas.bookingSchema import Book, BookingStatus

from core.security.security import verify_access_token

from routers.eventRoutes import get_authenticated_user

router = APIRouter()

@router.post("/book-seat/{event_id}")
async def book_seat(
    event_id: uuid.UUID,
    book: Book,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    try:
        async with db.begin():

            # 1. Authenticate user
            user = await get_authenticated_user(
                authorization=authorization,
                db=db
            )

            if user.role != UserRole.ATTENDEE:
                raise HTTPException(
                    status_code=403,
                    detail="You are not allowed to book events"
                )
            
            # 2. Find and lock event row
            event_result = await db.execute(
                select(Event)
                .where(Event.event_id == event_id)
                .with_for_update()
            )

            event = event_result.scalar_one_or_none()

            if event is None:
                raise HTTPException(
                    status_code=404,
                    detail="Event doesn't exist"
                )

            # 3. Check event eligibility
            if event.is_deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Event doesn't exist"
                )

            if event.status == Status.CANCELLED:
                raise HTTPException(
                    status_code=400,
                    detail="This event has been cancelled"
                )

            if event.status != Status.PUBLISHED:
                raise HTTPException(
                    status_code=400,
                    detail="This event is not published"
                )

            if event.start_time <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot book an event that has already started"
                )

            # 4. Check for an existing booking


            booking_check = await db.execute(
                select(Booking).where(
                    Booking.user_id == user.user_id,
                    Booking.event_id == event_id
                )
            )

            existing_booking = booking_check.scalar_one_or_none()

            print("6. Existing booking check completed")

            print("7. Calculating booked seats")

            if existing_booking is not None:
                raise HTTPException(
                    status_code=409,
                    detail="You have already booked this event"
                )

            # 5. Calculate confirmed seats already booked
            booking_result = await db.execute(
                select(
                    func.coalesce(func.sum(Booking.seats), 0)
                ).where(
                    Booking.event_id == event_id,
                    Booking.status == BookingStatus.CONFIRMED
                )
            )

            booked_seats = booking_result.scalar_one()
            available_seats = event.capacity - booked_seats

            # 6. Check requested seats
            if book.seats > available_seats:
                print("10. Insufficient seats — raising HTTPException")

                raise HTTPException(
                    status_code=409,
                    detail=f"Only {available_seats} seats are available"
                )

            # 7. Create booking
            new_booking = Booking(
                user_id=user.user_id,
                event_id=event_id,
                seats=book.seats,
                status=BookingStatus.CONFIRMED
            )

            db.add(new_booking)
            await db.flush()

            # Prepare response before the transaction commits
            response = {
                "message": "Booking created successfully",
                "booking_id": str(new_booking.booking_id),
                "event_id": str(new_booking.event_id),
                "seats": new_booking.seats,
                "status": new_booking.status.value
            }

        # Exiting db.begin() successfully commits the transaction.

        return response

    except IntegrityError as exc:
        print(f"Database integrity error: {exc}")

        raise HTTPException(
            status_code=409,
            detail="Booking conflicts with an existing database constraint"
        ) from exc



@router.patch("/cancel-seat/{booking_id}")
async def cancel_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    async with db.begin():
        user = await get_authenticated_user(authorization, db)

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

@router.get("/booked-seats/{event_id}")
async def get_booked_seats(
    event_id: uuid.UUID,
    authorization: str = Header(),
    db: AsyncSession = Depends(get_db),
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

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event doesn't exist",
        )

    if event.is_deleted:
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
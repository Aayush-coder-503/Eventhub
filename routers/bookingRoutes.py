
import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from schemas.bookingSchema import Book
from services.bookingServices import (
    book_seat as book_seat_service,
    cancel_booking as cancel_booking_service,
    get_booked_seats as get_booked_seats_service,
)

from core.security.dependencies import get_current_user

from models.userModels import User


router = APIRouter()


@router.post("/book-seat/{event_id}")
async def book_seat(
    event_id: uuid.UUID,
    book: Book,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await book_seat_service(
        event_id=event_id,
        book=book,
        user=user,
        db=db,
    )


@router.patch("/cancel-seat/{booking_id}")
async def cancel_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await cancel_booking_service(
        booking_id=booking_id,
        user=user,
        db=db,
    )


@router.get("/booked-seats/{event_id}")
async def get_booked_seats(
    event_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_booked_seats_service(
        event_id=event_id,
        user=user,
        db=db,
    )


from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from db.db import get_db
from models.userModels import User
from models.eventModels import Event
from models.categoryModels import Category
from schemas.authSchema import UserRole
from schemas.eventSchema import CreateEvent
from schemas.editeventSchema import EditEvent
from core.security.security import verify_access_token

router = APIRouter()


async def get_authenticated_user(
    authorization: str,
    db: AsyncSession,
):
    scheme, token = authorization.split(" ", 1)

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme",
        )

    payload = verify_access_token(token=token)

    user_id = payload["sub"]

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User doesn't exist",
        )

    return user


@router.get("/events")
async def events(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Event).where(Event.is_deleted.is_(False))
    )

    event_list = result.scalars().all()  # Fetch all matching events, not just one.

    return {"event_lists": event_list}


@router.post("/create-event")
async def create_event(
    event: CreateEvent,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
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
            "status": new_event.status,
            "category": category.category_names,
        }
    }


@router.patch("/edit-event/{event_id}")
async def edit_event(
    event_id: uuid.UUID,
    edit_event: EditEvent,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    user = await get_authenticated_user(authorization, db)

    if user.role != UserRole.ORGANIZER:
        raise HTTPException(
            status_code=403,
            detail="Only organizers can edit events",
        )

    result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    existing_event = result.scalar_one_or_none()

    if existing_event is None:
        raise HTTPException(
            status_code=404,
            detail="Event doesn't exist",
        )

    if str(existing_event.organizer_id) != str(user.user_id):
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

    await db.commit()
    await db.refresh(existing_event)

    return {
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
            "status": existing_event.status,
            "category_id": str(existing_event.category_id),
        },
    }


@router.delete("/delete-event/{event_id}")
async def delete_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    user = await get_authenticated_user(authorization, db)

    if user.role != UserRole.ORGANIZER:
        raise HTTPException(
            status_code=403,
            detail="Only organizers can delete events",
        )

    result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    existing_event = result.scalar_one_or_none()

    if existing_event is None:
        raise HTTPException(
            status_code=404,
            detail="Event doesn't exist",
        )

    if str(existing_event.organizer_id) != str(user.user_id):
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own events",
        )

    
    existing_event.is_deleted = True # Soft delete: keep the database record but hide the event.

    await db.commit()

    return {"message": "Deleted event successfully"}

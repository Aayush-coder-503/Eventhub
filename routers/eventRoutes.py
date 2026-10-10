import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from schemas.eventSchema import CreateEvent
from schemas.editeventSchema import EditEvent

from services.eventServices import (
    get_events,
    create_event as create_event_service,
    edit_event as edit_event_service,
    delete_event as delete_event_service,
)

router = APIRouter()


@router.get("/events")
async def events(
    db: AsyncSession = Depends(get_db),
):
    return await get_events(db=db)


@router.post("/create-event")
async def create_event(
    event: CreateEvent,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    return await create_event_service(
        event=event,
        authorization=authorization,
        db=db,
    )


@router.patch("/edit-event/{event_id}")
async def edit_event(
    event_id: uuid.UUID,
    edit_event: EditEvent,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    return await edit_event_service(
        event_id=event_id,
        edit_event=edit_event,
        authorization=authorization,
        db=db,
    )


@router.delete("/delete-event/{event_id}")
async def delete_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    return await delete_event_service(
        event_id=event_id,
        authorization=authorization,
        db=db,
    )

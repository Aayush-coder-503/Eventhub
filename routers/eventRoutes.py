import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query
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


@router.get("/events")
async def events(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    category_id: uuid.UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, max_length=100),
    sort_by: Literal["date", "price"] = "date",
    order: Literal["asc", "desc"] = "asc",
    db: AsyncSession = Depends(get_db),
):
    return await get_events(
        db=db,
        page=page,
        size=size,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        order=order,
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


from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from services.profileServices import get_user_profile

router = APIRouter()


@router.get("/profile")
async def profile(
    authorization: str = Header(),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_profile(
        authorization=authorization,
        db=db,
    )

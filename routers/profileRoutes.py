
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from services.profileServices import get_user_profile

from core.security.dependencies import get_current_user

from models.userModels import User


router = APIRouter()


@router.get("/profile")
async def profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_profile(
        user=user,
        db=db,
    )

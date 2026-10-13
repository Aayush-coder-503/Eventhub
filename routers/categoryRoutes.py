
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from schemas.categorySchema import Categories
from services.categoryServices import create_category as create_category_service

from core.security.dependencies import get_current_user

from models.userModels import User

router = APIRouter()


@router.post("/category")
async def create_category(
    category: Categories,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),

):
    return await create_category_service(
        category=category,
        user=user,
        db=db,
    )

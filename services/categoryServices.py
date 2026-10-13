
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.userModels import User
from models.categoryModels import Category
from schemas.authSchema import UserRole
from schemas.categorySchema import Categories
from core.security.security import verify_access_token


async def create_category(
    category: Categories,
    user:User,
    db: AsyncSession,
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create categories",
        )

    new_category = Category(
        category_id=uuid.uuid4(),
        category_names=category.category_names,
    )

    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    return {
        "Category": {
            "category_name": new_category.category_names,
        }
    }

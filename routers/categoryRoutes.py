from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from db.db import get_db
from models.userModels import User
from models.categoryModels import Category
from schemas.authSchema import UserRole
from schemas.categorySchema import Categories
from core.security.security import verify_access_token

router = APIRouter()

@router.post("/category")
async def create_category(
    category: Categories,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(),
):
    scheme, token = authorization.split(" ", 1)

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme",
        )

    verified_token = verify_access_token(token=token)
    user_id = verified_token["sub"]

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User doesn't exist",
        )

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
            "category_name": new_category.category_names
        }
    }

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from schemas.authSchema import RegisterUsers, LoginUsers
from services.authServices import register_user, login_user


router = APIRouter()


@router.post("/register")
async def user_register(
    user: RegisterUsers,
    db: AsyncSession = Depends(get_db),
):
    return await register_user(user=user, db=db)


@router.post("/login")
async def user_login(
    login: LoginUsers,
    db: AsyncSession = Depends(get_db),
):
    return await login_user(login=login, db=db)

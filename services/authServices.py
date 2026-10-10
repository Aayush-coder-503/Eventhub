
import uuid
import bcrypt

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.userModels import User
from schemas.authSchema import RegisterUsers, LoginUsers
from core.security.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)


async def register_user(
    user: RegisterUsers,
    db: AsyncSession,
):
    result = await db.execute(
        select(User).where(User.email == user.email)
    )
    user_exist = result.scalar_one_or_none()

    if user_exist:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        user_id=uuid.uuid4(),
        name=user.user_name,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.ATTENDEE,
    )

    access_token = create_access_token(new_user.user_id)
    refresh_token = create_refresh_token(new_user.user_id)

    new_user.hashed_refresh_token = hash_refresh_token(
        refresh_token
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "user": {
            "name": new_user.name,
            "email": new_user.email,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "role": new_user.role.value,
        }
    }


async def login_user(
    login: LoginUsers,
    db: AsyncSession,
):
    result = await db.execute(
        select(User).where(User.email == login.email)
    )
    user_exist = result.scalar_one_or_none()

    if not user_exist:
        raise HTTPException(
            status_code=404,
            detail="User doesn't exist",
        )

    password_correct = bcrypt.checkpw(
        login.password.encode("utf-8"),
        user_exist.hashed_password.encode("utf-8"),
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        str(user_exist.user_id)
    )
    refresh_token = create_refresh_token(
        str(user_exist.user_id)
    )

    user_exist.hashed_refresh_token = hash_refresh_token(
        refresh_token
    )

    await db.commit()

    return {
        "name": user_exist.name,
        "role": user_exist.role.value,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "message": "Logged in successfully",
    }

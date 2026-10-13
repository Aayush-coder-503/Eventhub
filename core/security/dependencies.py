import uuid

from fastapi import HTTPException, Cookie, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.userModels import User
from core.security.security import verify_access_token

from db.db import get_db


async def get_authenticated_user(
    authorization: str,
    db: AsyncSession,
):
    try:
        scheme, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

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


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Access token cookie is missing",
        )

    try:
        payload = verify_access_token(token=access_token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists",
        )

    return user

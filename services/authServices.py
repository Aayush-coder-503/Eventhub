import uuid
import bcrypt
import hmac

from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.userModels import User
from schemas.authSchema import RegisterUsers, LoginUsers, UserRole
from core.security.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_refresh_token
)


async def register_user(
    user: RegisterUsers,
    response: Response,
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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=15 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )

    new_user.hashedRefreshToken = hash_refresh_token(
        refresh_token
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "user": {
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role.value,
        }
    }


async def login_user(
    login: LoginUsers,
    response: Response,
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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=15 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )


    user_exist.hashedRefreshToken = hash_refresh_token(
        refresh_token
    )

    await db.commit()

    return {
        "name": user_exist.name,
        "role": user_exist.role.value,
    }



async def refresh_tokens_service(
    refresh_token: str,
    db: AsyncSession,
):
    try:
        payload = verify_refresh_token(refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token payload",
        )

    result = await db.execute(
        select(User)
        .where(User.user_id == user_id)
        .with_for_update()
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    incoming_hash = hash_refresh_token(refresh_token)

    if not user.hashedRefreshToken or not hmac.compare_digest(
        user.hashedRefreshToken,
        incoming_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid or has already been used",
        )

    new_access_token = create_access_token(str(user.user_id))
    new_refresh_token = create_refresh_token(str(user.user_id))

    user.hashedRefreshToken = hash_refresh_token(new_refresh_token)

    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }

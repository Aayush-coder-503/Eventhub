
from fastapi import APIRouter, Depends, Cookie, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from schemas.authSchema import RegisterUsers, LoginUsers
from services.authServices import register_user, login_user, refresh_tokens_service


router = APIRouter()


@router.post("/register")
async def user_register(
    user: RegisterUsers,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await register_user(user=user, db=db, response=response)


@router.post("/login")
async def user_login(
    login: LoginUsers,
    response:Response,
    db: AsyncSession = Depends(get_db),
):
    return await login_user(login=login, db=db, response=response)


@router.post("/refresh")
async def refresh_tokens(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Refresh token cookie is missing",
        )

    tokens = await refresh_tokens_service(
        refresh_token=refresh_token,
        db=db,
    )

    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=15 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )

    return {
        "message": "Tokens refreshed successfully",
    }

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from models.authModels import UserRole, RegisterUsers, LoginUsers
from schemas.userSchema import User
from db.db import Base, engine, get_db
import uuid
import bcrypt

from core.security.security import (
    hash_password,
    create_access_token,
    verify_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_refresh_token
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession



app = FastAPI()


@app.get('/')
async def root():
    return {'project': 'EventHub'}


@app.post('/register')
async def user_register(
    user: RegisterUsers,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == user.email)
    )

    #result is not the User object.
    #It's a SQLAlchemy Result object containing the result of the query.
    #So we need to extract the User from that result:
    
    user_exist = result.scalar_one_or_none()

    if user_exist:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        user_id=uuid.uuid4(),
        name=user.user_name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )

    access_token = create_access_token(
        str(new_user.user_id)
    )

    refresh_token = create_refresh_token(
        str(new_user.user_id)
    )

    hashed_refresh_token = hash_refresh_token(
        refresh_token
    )

    new_user.hashedRefreshToken = hashed_refresh_token

    #Not await because adding the object to SQLAlchemy's session doesn't itself send the SQL to PostgreSQL
    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return {
        "user": {
            "name": new_user.name,
            "email": new_user.email,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "role": new_user.role.value
        },
    }


@app.post('/login')
async def user_login(
    login: LoginUsers,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == login.email)
    )

    user_exist = result.scalar_one_or_none()

    if not user_exist:
        raise HTTPException(
            status_code=409,
            detail="User don't exist"
        )

    password_correct = bcrypt.checkpw(
        login.password.encode("utf-8"),
        user_exist.hashed_password.encode("utf-8")
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        str(user_exist.user_id)
    )

    refresh_token = create_refresh_token(
        str(user_exist.user_id)
    )

    hashed_refresh_token = hash_refresh_token(
        refresh_token
    )

    user_exist.hashed_refresh_token = hashed_refresh_token

    await db.commit()

    return {
        "name": user_exist.name,
        "role": user_exist.role,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "message": "Logged in successfully"
    }


#'/refresh  --- Pending [An endpoint to make refresh the accesstoken if expired]'

@app.post("/create-event")
async def create_event(authorization: str = Header()):
    scheme, token = authorization.split(" ")
    return {"Scheme": scheme, "Token": token}

    #{inside a function

    #Get a token from the req header BEARER {token}
    
    #Verify the token

    #Get user_id and verify a email

    #Get a role of the user if role is Organizer give allow to create a event

    # return boolean is_allowed? true | false and user_id}

    #if true

    #Create a uuuid for event id

    #Create title, description, venue, starttime, endtime, capacity, price

    #Get a category id from category table

    #Get a organizer id which is user_id

    #Set a status [draft, published, cancelled]

    #created_at and updated_at

    #"""
    #add(new_user)
    #await commit()
    #await refresh(new_user)
    #"""






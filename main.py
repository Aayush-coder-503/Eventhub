from fastapi import FastAPI, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session

from models.authModels import UserRole, RegisterUsers, LoginUsers
from schemas.userSchema import User

from models.eventModels import CreateEvent
from schemas.eventSchema import Event

from models.editeventModels import EditEvent

from models.categoryModels import Categories
from schemas.categorySchema import Category

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

    #Adding hashed refresh token to table
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


#'/refresh'  --- Pending [An endpoint to make refresh the accesstoken if expired]'

@app.post("/category")
async def create_category(
    category: Categories = Body(...),
    db:AsyncSession = Depends(get_db),
    authorization: str = Header()
    ):

    scheme, token = authorization.split(" ")

    verified_token = verify_access_token(token=token)

    user_id = verified_token["sub"]

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )

    user = result.scalar_one_or_none()

    role = user.role

    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create categories"
        )
    
    new_category = Category(
        category_id=uuid.uuid4(),
        category_names=category
    )

    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    return{
        "Category":{
            "category_name": new_category.category_names
        }
    }



@app.post("/create-event")
async def create_event(
    event:CreateEvent,
    db:AsyncSession = Depends(get_db),
    authorization: str = Header()
    ):


    scheme, token = authorization.split(" ")
    
    verified_token = verify_access_token(token=token)


    user_id = verified_token["sub"]

    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )

    user = result.scalar_one_or_none()

    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User doesn't exist"
        )
    

    role = user.role
    if role != UserRole.ORGANIZER:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create-event"
        )

    category_result = await db.execute(
        select(Category).where(
            Category.category_id == event.category_id
        )
    )

    category = category_result.scalar_one_or_none()


    if category is None:
        raise HTTPException(
        status_code=404,
        detail="Category doesn't exist"
    )

    new_event = Event(
        event_id=uuid.uuid4(),
        title=event.title,
        description=event.description,
        venue=event.venue,
        start_time=event.start_time,
        end_time=event.end_time,
        capacity=event.capacity,
        price=event.price,
        organizer_id=user_id,
        category_id=event.category_id,
        status=event.status
    )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    return{
        "event":{
            "title":new_event.title,
            "description": new_event.description,
            "venue": new_event.venue,
            "start_time":new_event.start_time,
            "end_time":new_event.end_time,
            "capacity": new_event.capacity,
            "price": new_event.price,
            "status":new_event.status,
            "category":category.category_names
        }
    }


@app.patch('/edit-event/{event_id}')
async def edit_event(
    event_id: uuid.UUID,
    edit_event: EditEvent, 
    db: AsyncSession = Depends(get_db),
    authorization: str = Header()
    ):
    
    scheme, token = authorization.split(" ")

    #First verify the token
    verify_token = verify_access_token(token=token)
    user_id = verify_token['sub']

    #verify the user
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User doesn't exist"
        )

    #give access to edit only for the organizer
    role = user.role
    if role != UserRole.ORGANIZER:
        raise HTTPException(
            status_code=403,
            detail="Only organizers can edit events"
        )

    
    # 4. Find the existing event
    result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    existing_event = result.scalar_one_or_none()

    if existing_event is None:
        raise HTTPException(
            status_code=404,
            detail="Event doesn't exist"
        )

    # 5. Ensure this organizer owns the event
    if existing_event.organizer_id != str(user.user_id):
        print("Authenticated user ID:", user.user_id, type(user.user_id))
        print("Event organizer ID:", existing_event.organizer_id, type(existing_event.organizer_id))
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own events"
        )

    # 6. Get only the fields the client provided
    update_data = edit_event.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update"
        )
    
    # 7. Validate category only if category_id was provided
    if "category_id" in update_data:
        category_result = await db.execute(
            select(Category).where(
                Category.category_id == update_data["category_id"]
            )
        )
        category = category_result.scalar_one_or_none()

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Category doesn't exist"
            )
    
    # 8. Update only the provided fields
    for field, value in update_data.items():
        setattr(existing_event, field, value)

    await db.commit()
    await db.refresh(existing_event)

    return {
        "message": "Event updated successfully",
        "event": {
            "title": existing_event.title,
            "description": existing_event.description,
            "venue": existing_event.venue,
            "start_time": existing_event.start_time,
            "end_time": existing_event.end_time,
            "capacity": existing_event.capacity,
            "price": existing_event.price,
            "status": existing_event.status,
            "category_name": str(existing_event.event_id)
        }
    }
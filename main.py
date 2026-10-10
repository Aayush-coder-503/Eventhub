from contextlib import asynccontextmanager
from fastapi import FastAPI

from db.db import engine
from routers import (
    authRoutes,
    eventRoutes,
    categoryRoutes,
    bookingRoutes,
    profileRoutes,
)


API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as connection:
        await connection.run_sync(lambda conn: None)

    print("EventHub API started successfully")

    yield

    await engine.dispose()
    print("EventHub API shut down successfully")


app = FastAPI(
    title="EventHub API",
    description="API for event management and seat booking",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
async def status():
    return {
        "message": "EventHub server is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


#Routers
app.include_router(authRoutes.router, prefix=API_V1_PREFIX)
app.include_router(eventRoutes.router, prefix=API_V1_PREFIX)
app.include_router(categoryRoutes.router, prefix=API_V1_PREFIX)
app.include_router(bookingRoutes.router, prefix=API_V1_PREFIX)
app.include_router(profileRoutes.router, prefix=API_V1_PREFIX)

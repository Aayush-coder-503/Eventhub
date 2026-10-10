from fastapi import FastAPI
from routers import authRoutes, eventRoutes, categoryRoutes, bookingRoutes, profileRoutes

app = FastAPI()


@app.get("/")
async def status():
    return {"message": "server is running"}


# Routers
app.include_router(authRoutes.router)
app.include_router(eventRoutes.router)
app.include_router(categoryRoutes.router)
app.include_router(bookingRoutes.router)
app.include_router(profileRoutes.router)


#IMP ADD VERSIONS AND ALSO LIFESPAN AND LIFECYCLE FOR FASTAPI
from fastapi import FastAPI
from routers import authRoutes, eventRoutes, categoryRoutes

app = FastAPI()


@app.get("/")
async def status():
    return {"message": "server is running"}


# Routers
app.include_router(authRoutes.router)
app.include_router(eventRoutes.router)
app.include_router(categoryRoutes.router)


#IMP ADD VERSIONS AND ALSO LIFESPAN AND LIFECYCLE FOR FASTAPI
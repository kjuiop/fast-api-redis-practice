from fastapi import FastAPI

from app.core import lifespan
from app.routers import auth, items, recent_views, users


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(recent_views.router)
app.include_router(users.router)
app.include_router(items.router)


@app.get("/", tags=["root"])
def read_root():
    return {"Hello": "World"}
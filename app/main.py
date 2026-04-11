from fastapi import FastAPI

from app.core import lifespan
from app.routers import articles, auth, items, recent_views, stock, users


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(recent_views.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(articles.router)
app.include_router(stock.router)

@app.get("/", tags=["root"])
def read_root():
    return {"Hello": "World"}
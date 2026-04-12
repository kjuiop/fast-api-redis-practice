from fastapi import FastAPI

from app.core import lifespan
from app.middleware.token_bucket_limit import register_token_bucket_middleware
from app.routers import articles, auth, items, recent_views, stock, users, rank, pub_sub


app = FastAPI(lifespan=lifespan)

register_token_bucket_middleware(app)

app.include_router(auth.router)
app.include_router(recent_views.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(articles.router)
app.include_router(stock.router)
app.include_router(rank.router)
app.include_router(pub_sub.router)

@app.get("/", tags=["root"])
def read_root():
    return {"Hello": "World"}

@app.get("/data")
async def get_sensitive_data():
    return {"data": "This is protected by rate limiting"}
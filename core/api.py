import fastapi
from fastapi import FastAPI
from .store import router as store_router
from .main import app as user_router

app=FastAPI(
    title="E-commerce")
    

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(store_router, tags=["store"])
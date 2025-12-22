from fastapi import FastAPI
from src.app.api_overview import router as overview_router

app = FastAPI()

app.include_router(overview_router, prefix="/api")

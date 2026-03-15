from fastapi import FastAPI
from app.api.import_routes import router as import_router

app = FastAPI(title="AI Import Service", version="0.2.0")
app.include_router(import_router, prefix="/api")

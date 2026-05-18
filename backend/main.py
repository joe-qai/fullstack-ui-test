from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db.database import engine, Base
from api.projects import router as projects_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)

@app.get("/")
def root():
    return {"message": "UI AutoTest Platform API"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import (
    auth, data, users,
    super_admin, community_admin, community_coordinator, 
    settings, feed, events
)
from dotenv import load_dotenv
load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API (fixed)")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(data.router)
app.include_router(super_admin.router)
app.include_router(community_admin.router)
app.include_router(community_coordinator.router)
app.include_router(settings.router)
app.include_router(feed.router)
app.include_router(events.router)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from database import Base, engine
from routers import (
    auth, data, users,
    super_admin, community_admin, community_coordinator, 
    settings, feed, events, analytics
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
app.include_router(analytics.router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Auth API (fixed)",
        version="1.0.0",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply to all endpoints automatically
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

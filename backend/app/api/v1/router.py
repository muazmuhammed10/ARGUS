"""
ARGUS — API v1 router: aggregates all sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, dashboard, events, incidents, assets,
    rules, investigations, intelligence, reports, ai,
    alerts, users,
)

api_router = APIRouter()

api_router.include_router(auth.router,            prefix="/auth",            tags=["Authentication"])
api_router.include_router(dashboard.router,       prefix="/dashboard",       tags=["Dashboard"])
api_router.include_router(events.router,          prefix="/events",          tags=["Security Events"])
api_router.include_router(incidents.router,       prefix="/incidents",       tags=["Incidents"])
api_router.include_router(alerts.router,          prefix="/alerts",          tags=["Alerts"])
api_router.include_router(assets.router,          prefix="/assets",          tags=["Assets"])
api_router.include_router(rules.router,           prefix="/rules",           tags=["Detection Rules"])
api_router.include_router(investigations.router,  prefix="/investigations",  tags=["Investigations"])
api_router.include_router(intelligence.router,    prefix="/intelligence",    tags=["Threat Intelligence"])
api_router.include_router(reports.router,         prefix="/reports",         tags=["Reports"])
api_router.include_router(ai.router,              prefix="/ai",              tags=["AI Analysis"])
api_router.include_router(users.router,           prefix="/users",           tags=["User Management"])

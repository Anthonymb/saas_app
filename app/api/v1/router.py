from app.api.v1.endpoints.audit import router as audit_router
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.campaigns import router as campaigns_router
from app.api.v1.endpoints.contacts import router as contacts_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(audit_router)
api_router.include_router(campaigns_router)
api_router.include_router(contacts_router)
api_router.include_router(jobs_router)
api_router.include_router(payments_router)
api_router.include_router(users_router)
api_router.include_router(webhooks_router)

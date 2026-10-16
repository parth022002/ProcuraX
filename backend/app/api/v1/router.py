from fastapi import APIRouter
from app.api.v1.routes import analytics, auth, cases, copilot, evaluation, health, impact, risk, scenarios, signals, suppliers

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(suppliers.router)
api_router.include_router(signals.router)
api_router.include_router(risk.router)
api_router.include_router(impact.router)
api_router.include_router(scenarios.router)
api_router.include_router(copilot.router)
api_router.include_router(cases.router)
api_router.include_router(evaluation.router)
api_router.include_router(analytics.router)

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.accounts import router as accounts_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.mode import router as mode_router
from app.api.routes.rules import router as rules_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.reports import router as reports_router
from app.api.routes.simulation import router as simulation_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(mode_router, prefix="/mode", tags=["mode"])
api_router.include_router(rules_router, prefix="/rules", tags=["rules"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(simulation_router, prefix="/simulation", tags=["simulation"])

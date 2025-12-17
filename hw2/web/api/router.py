from fastapi.routing import APIRouter

from hw2.web.api import endpoints, monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(endpoints.router)

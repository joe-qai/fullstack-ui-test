from fastapi import APIRouter
from api.projects import router as projects_router
from api.pages import router as pages_router
from api.keywords import router as keywords_router
from api.cases import router as cases_router
from api.scripts import router as scripts_router
from api.devices import router as devices_router
from api.tasks import router as tasks_router
from api.debug import router as debug_router
from api.apks import router as apks_router

api_router = APIRouter()
api_router.include_router(projects_router)
api_router.include_router(pages_router)
api_router.include_router(keywords_router)
api_router.include_router(cases_router)
api_router.include_router(scripts_router)
api_router.include_router(devices_router)
api_router.include_router(tasks_router)
api_router.include_router(debug_router)
api_router.include_router(apks_router)

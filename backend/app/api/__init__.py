from fastapi import APIRouter

from app.api import admin, auth, finance, lessons, me, parent, students

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(students.router)
api_router.include_router(lessons.router)
api_router.include_router(finance.router)
api_router.include_router(me.router)
api_router.include_router(parent.router)


@api_router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_roles
from app.models import Role, User
from app.schemas.dashboard import DashboardStats
from app.services.dashboard import dashboard_stats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
async def stats(
    user: User = Depends(require_roles(Role.teacher, Role.superuser)),
    db: AsyncSession = Depends(get_db),
):
    if user.role != Role.teacher:
        # Аналитика практики — у учителя; суперюзер смотрит через режим просмотра
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Дашборд доступен учителю (войдите от имени учителя)",
        )
    return await dashboard_stats(db, teacher_id=user.id)

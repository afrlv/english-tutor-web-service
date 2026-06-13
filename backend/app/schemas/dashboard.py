from decimal import Decimal

from pydantic import BaseModel


class MonthEarning(BaseModel):
    month: str  # "2026-06"
    earned: Decimal


class DebtorRow(BaseModel):
    student_id: int
    student_name: str
    debt: Decimal


class DashboardStats(BaseModel):
    earned_this_month: Decimal
    earned_prev_month: Decimal
    earned_total: Decimal
    monthly: list[MonthEarning]  # последние 6 месяцев, по возрастанию

    debt_total: Decimal
    top_debtors: list[DebtorRow]

    students_total: int
    students_active: int  # был проведённый урок за 30 дней
    students_quiet: int  # нет уроков > 30 дней (ранний отток)

    lessons_week_conducted: int
    lessons_week_planned: int
    lessons_month_conducted: int

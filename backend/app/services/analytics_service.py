from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.entities import Transaction
from app.services.budget_service import get_period_dates

def get_cashflow_analytics(db: Session, user_id: int, period: str) -> Dict[str, Any]:
    start_dt, end_dt = get_period_dates(period)

    # Fetch completed transactions within the period (§8, §13)
    completed_txs = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.status == "completed",
        Transaction.created_at >= start_dt,
        Transaction.created_at < end_dt
    ).order_by(Transaction.created_at.asc()).all()

    daily_data = defaultdict(lambda: {"income_paise": 0, "expenses_paise": 0})

    total_income = 0
    total_expenses = 0

    for tx in completed_txs:
        day_str = tx.created_at.strftime("%Y-%m-%d")
        if tx.type == "income":
            daily_data[day_str]["income_paise"] += tx.amount_paise
            total_income += tx.amount_paise
        elif tx.type == "expense":
            daily_data[day_str]["expenses_paise"] += tx.amount_paise
            total_expenses += tx.amount_paise

    daily_points = []
    for day in sorted(daily_data.keys()):
        inc = daily_data[day]["income_paise"]
        exp = daily_data[day]["expenses_paise"]
        daily_points.append({
            "date": day,
            "income_paise": inc,
            "expenses_paise": exp,
            "net_paise": inc - exp
        })

    return {
        "period": period,
        "total_income_paise": total_income,
        "total_expenses_paise": total_expenses,
        "net_cashflow_paise": total_income - total_expenses,
        "daily": daily_points
    }

def get_category_analytics(db: Session, user_id: int, period: str) -> Dict[str, Any]:
    start_dt, end_dt = get_period_dates(period)

    completed_expenses = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.status == "completed",
        Transaction.created_at >= start_dt,
        Transaction.created_at < end_dt
    ).all()

    total_spent = sum(tx.amount_paise for tx in completed_expenses)
    cat_spent = defaultdict(int)

    for tx in completed_expenses:
        cat = tx.category or "General"
        cat_spent[cat] += tx.amount_paise

    breakdown = []
    for cat, amount in sorted(cat_spent.items(), key=lambda x: x[1], reverse=True):
        pct = round((amount / total_spent) * 100, 1) if total_spent > 0 else 0.0
        breakdown.append({
            "category": cat,
            "amount_paise": amount,
            "percentage": pct
        })

    return {
        "period": period,
        "total_spent_paise": total_spent,
        "categories": breakdown
    }

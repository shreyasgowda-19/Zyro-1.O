from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.entities import Budget, Transaction
from app.services.alert_service import create_alert
from app.clock import utcnow
from app.errors import AppError

def get_period_dates(period: str):
    try:
        parts = period.split("-")
        year, month = int(parts[0]), int(parts[1])
        start_dt = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        else:
            end_dt = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return start_dt, end_dt
    except Exception:
        now = utcnow()
        start_dt = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if now.month == 12:
            end_dt = datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        else:
            end_dt = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return start_dt, end_dt

def get_user_budgets(db: Session, user_id: int, period: Optional[str] = None) -> List[Budget]:
    query = db.query(Budget).filter(Budget.user_id == user_id)
    if period:
        query = query.filter(Budget.period == period)
    return query.order_by(Budget.category.asc().nullsfirst()).all()

def create_or_update_budget(
    db: Session,
    user_id: int,
    category: Optional[str],
    amount_paise: int,
    period: str
) -> Budget:
    clean_cat = category.strip() if category and category.strip() else None

    # Check if budget already exists for this period and category
    existing = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.period == period,
        Budget.category == clean_cat
    ).first()

    if existing:
        existing.amount_paise = amount_paise
        budget = existing
    else:
        budget = Budget(
            user_id=user_id,
            category=clean_cat,
            amount_paise=amount_paise,
            period=period,
            created_at=utcnow()
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)

    # Evaluate budget alerts after budget update (§13)
    evaluate_budget_alerts(db, user_id, period)

    return budget

def update_budget(db: Session, user_id: int, budget_id: int, amount_paise: int) -> Budget:
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not budget:
        raise AppError("NOT_FOUND", "Budget not found", status_code=404)

    budget.amount_paise = amount_paise
    db.commit()
    db.refresh(budget)

    evaluate_budget_alerts(db, user_id, budget.period)
    return budget

def delete_budget(db: Session, user_id: int, budget_id: int) -> bool:
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not budget:
        raise AppError("NOT_FOUND", "Budget not found", status_code=404)

    db.delete(budget)
    db.commit()
    return True

def get_budget_summary(db: Session, user_id: int, period: str) -> Dict[str, Any]:
    start_dt, end_dt = get_period_dates(period)

    # 1. Fetch completed expenses strictly within period (§8, §13)
    completed_expenses = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.status == "completed",
        Transaction.created_at >= start_dt,
        Transaction.created_at < end_dt
    ).all()

    total_spent_paise = sum(tx.amount_paise for tx in completed_expenses)

    category_spent: Dict[str, int] = {}
    for tx in completed_expenses:
        cat = tx.category or "General"
        category_spent[cat] = category_spent.get(cat, 0) + tx.amount_paise

    # 2. Fetch all user budgets for this period
    budgets = get_user_budgets(db, user_id, period)
    overall_budget = next((b for b in budgets if b.category is None), None)

    overall_budget_paise = overall_budget.amount_paise if overall_budget else None
    overall_pct = (
        round((total_spent_paise / overall_budget_paise) * 100, 1)
        if overall_budget_paise and overall_budget_paise > 0
        else None
    )
    overall_rem = (
        max(0, overall_budget_paise - total_spent_paise)
        if overall_budget_paise is not None
        else None
    )

    overall_summary = {
        "budget_paise": overall_budget_paise,
        "spent_paise": total_spent_paise,
        "remaining_paise": overall_rem,
        "percentage": overall_pct
    }

    # 3. Build category summaries
    category_budgets: Dict[str, Budget] = {
        b.category: b for b in budgets if b.category is not None
    }
    all_categories = sorted(list(set(category_budgets.keys()) | set(category_spent.keys())))

    categories_list = []
    for cat in all_categories:
        b_entry = category_budgets.get(cat)
        b_paise = b_entry.amount_paise if b_entry else None
        s_paise = category_spent.get(cat, 0)
        c_pct = (
            round((s_paise / b_paise) * 100, 1)
            if b_paise and b_paise > 0
            else None
        )
        c_rem = max(0, b_paise - s_paise) if b_paise is not None else None

        categories_list.append({
            "category": cat,
            "budget_paise": b_paise,
            "spent_paise": s_paise,
            "remaining_paise": c_rem,
            "percentage": c_pct
        })

    return {
        "period": period,
        "overall": overall_summary,
        "categories": categories_list
    }

def evaluate_budget_alerts(db: Session, user_id: int, period: Optional[str] = None):
    """
    Evaluates 80% and 100% budget thresholds based on COMPLETED spending only (§13).
    Deduplication key: (budget id, period, threshold, budget amount)
    """
    if not period:
        period = utcnow().strftime("%Y-%m")

    summary = get_budget_summary(db, user_id, period)

    # 1. Evaluate Overall Budget Alert
    ov = summary["overall"]
    if ov["budget_paise"] is not None and ov["budget_paise"] > 0:
        spent = ov["spent_paise"]
        budget = ov["budget_paise"]
        pct = (spent / budget) * 100

        if spent >= budget:
            # 100% Exceeded Alert
            create_alert(
                db=db,
                user_id=user_id,
                alert_type="budget",
                title_code="alert.budget.limit_exceeded",
                params={
                    "category": "Overall",
                    "percentage": round(pct, 1),
                    "spent_paise": spent,
                    "budget_paise": budget
                },
                dedupe_key=f"budget_100_{user_id}_{period}_overall_{budget}"
            )
        elif spent >= int(budget * 0.8):
            # 80% Approaching Warning Alert
            create_alert(
                db=db,
                user_id=user_id,
                alert_type="budget",
                title_code="alert.budget.approaching_limit",
                params={
                    "category": "Overall",
                    "percentage": round(pct, 1),
                    "spent_paise": spent,
                    "budget_paise": budget
                },
                dedupe_key=f"budget_80_{user_id}_{period}_overall_{budget}"
            )

    # 2. Evaluate Per-Category Budget Alerts
    for cat_item in summary["categories"]:
        if cat_item["budget_paise"] is not None and cat_item["budget_paise"] > 0:
            spent = cat_item["spent_paise"]
            budget = cat_item["budget_paise"]
            pct = (spent / budget) * 100
            cat_name = cat_item["category"]

            if spent >= budget:
                create_alert(
                    db=db,
                    user_id=user_id,
                    alert_type="budget",
                    title_code="alert.budget.limit_exceeded",
                    params={
                        "category": cat_name,
                        "percentage": round(pct, 1),
                        "spent_paise": spent,
                        "budget_paise": budget
                    },
                    dedupe_key=f"budget_100_{user_id}_{period}_{cat_name}_{budget}"
                )
            elif spent >= int(budget * 0.8):
                create_alert(
                    db=db,
                    user_id=user_id,
                    alert_type="budget",
                    title_code="alert.budget.approaching_limit",
                    params={
                        "category": cat_name,
                        "percentage": round(pct, 1),
                        "spent_paise": spent,
                        "budget_paise": budget
                    },
                    dedupe_key=f"budget_80_{user_id}_{period}_{cat_name}_{budget}"
                )

    db.commit()

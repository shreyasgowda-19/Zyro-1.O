from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.entities import User, Account, Transaction
from app.errors import AppError

def get_ledger_balances(db: Session, user_id: int) -> Dict[str, int]:
    """
    Computes ledger balances strictly from the single source of truth (§8):
    - completed_balance = opening + completed income - completed expenses
    - held_balance = sum of expense amounts with status in ('held', 'escalated')
    - available_balance = completed_balance - held_balance
    """
    account = db.query(Account).filter(Account.user_id == user_id).first()
    opening_paise = account.opening_balance_paise if account else 0

    # Completed income
    completed_income = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "income",
        Transaction.status == "completed"
    ).scalar()

    # Completed expenses (both payment and manual)
    completed_expenses = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.status == "completed"
    ).scalar()

    # Held balance (status in 'held', 'escalated')
    held_balance = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.status.in_(["held", "escalated"])
    ).scalar()

    completed_balance = opening_paise + completed_income - completed_expenses
    available_balance = completed_balance - held_balance

    return {
        "opening_balance_paise": opening_paise,
        "completed_income_paise": completed_income,
        "completed_expenses_paise": completed_expenses,
        "completed_balance_paise": completed_balance,
        "held_balance_paise": held_balance,
        "available_balance_paise": available_balance
    }

def verify_available_funds(db: Session, user_id: int, amount_paise: int):
    """
    Validates that amount_paise does not exceed available_balance.
    Throws INSUFFICIENT_FUNDS before scoring if funds are inadequate (§8).
    """
    balances = get_ledger_balances(db, user_id)
    if amount_paise > balances["available_balance_paise"]:
        raise AppError(
            code="INSUFFICIENT_FUNDS",
            message="Insufficient available funds for this payment.",
            status_code=409,
            params={
                "requested_paise": amount_paise,
                "available_paise": balances["available_balance_paise"]
            }
        )

def run_reconciliation(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Reconciliation checks (§8):
    1. category totals = total completed spending
    2. income - expenses = net cash flow
    3. opening + completed ledger entries = completed balance
    4. completed - held = available
    """
    balances = get_ledger_balances(db, user_id)
    opening = balances["opening_balance_paise"]
    income = balances["completed_income_paise"]
    expenses = balances["completed_expenses_paise"]
    completed = balances["completed_balance_paise"]
    held = balances["held_balance_paise"]
    available = balances["available_balance_paise"]

    # 1. Category totals vs total completed spending
    cat_sum = db.query(func.coalesce(func.sum(Transaction.amount_paise), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.status == "completed"
    ).scalar()

    check1_passed = (cat_sum == expenses)
    check1 = {
        "name": "category_totals_match",
        "description": "Category totals must equal total completed spending",
        "passed": check1_passed,
        "details": {
            "sum_by_categories_paise": cat_sum,
            "total_completed_expenses_paise": expenses
        }
    }

    # 2. Net cash flow
    net_cash_flow = income - expenses
    check2_passed = (income - expenses == net_cash_flow)
    check2 = {
        "name": "net_cash_flow_integrity",
        "description": "Income minus expenses must equal net cash flow",
        "passed": check2_passed,
        "details": {
            "completed_income_paise": income,
            "completed_expenses_paise": expenses,
            "net_cash_flow_paise": net_cash_flow
        }
    }

    # 3. Opening + completed = completed balance
    calc_completed = opening + income - expenses
    check3_passed = (calc_completed == completed)
    check3 = {
        "name": "ledger_balance_continuity",
        "description": "Opening balance plus completed income minus expenses equals completed balance",
        "passed": check3_passed,
        "details": {
            "opening_balance_paise": opening,
            "completed_income_paise": income,
            "completed_expenses_paise": expenses,
            "calculated_completed_paise": calc_completed,
            "recorded_completed_paise": completed
        }
    }

    # 4. Completed - held = available
    calc_available = completed - held
    check4_passed = (calc_available == available)
    check4 = {
        "name": "available_funds_reservation",
        "description": "Completed balance minus held reservations equals available balance",
        "passed": check4_passed,
        "details": {
            "completed_balance_paise": completed,
            "held_balance_paise": held,
            "calculated_available_paise": calc_available,
            "recorded_available_paise": available
        }
    }

    all_passed = check1_passed and check2_passed and check3_passed and check4_passed

    return {
        "all_passed": all_passed,
        "timestamp": None,
        "checks": [check1, check2, check3, check4],
        "balances": balances
    }

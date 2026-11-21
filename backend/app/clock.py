from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz
from app.config import settings

IST = pytz.timezone("Asia/Kolkata")

class Clock:
    def __init__(self, fixed_now: Optional[datetime] = None):
        self._fixed_now = fixed_now

    def now_utc(self) -> datetime:
        if self._fixed_now:
            if self._fixed_now.tzinfo is None:
                return self._fixed_now.replace(tzinfo=timezone.utc)
            return self._fixed_now.astimezone(timezone.utc)
        return datetime.now(timezone.utc)

    def now_ist(self) -> datetime:
        return self.now_utc().astimezone(IST)

    def set_fixed_now(self, dt: Optional[datetime]):
        self._fixed_now = dt

clock = Clock()

def utcnow() -> datetime:
    return clock.now_utc()

def validate_and_resolve_time(simulated_at: Optional[datetime], current_clock: Optional[Clock] = None) -> datetime:
    clk = current_clock or clock
    current_utc = clk.now_utc()
    
    if simulated_at is None:
        return current_utc
        
    if not settings.DEMO_MODE:
        from app.errors import AppError
        raise AppError(code="DEMO_MODE_DISABLED", message="Simulated time is disabled when DEMO_MODE is false", status_code=400)
        
    # Ensure timezone aware
    sim_utc = simulated_at if simulated_at.tzinfo else simulated_at.replace(tzinfo=timezone.utc)
    sim_utc = sim_utc.astimezone(timezone.utc)
    
    min_time = current_utc - timedelta(days=30)
    max_time = current_utc + timedelta(days=1)
    
    if not (min_time <= sim_utc <= max_time):
        from app.errors import AppError
        raise AppError(
            code="VALIDATION_ERROR",
            message="simulated_at must be within [now - 30 days, now + 1 day]",
            status_code=422,
            params={"min_time": min_time.isoformat(), "max_time": max_time.isoformat()}
        )
        
    return sim_utc

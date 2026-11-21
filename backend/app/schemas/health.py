from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    schema_head: str
    rules_version: str
    demo_mode: bool

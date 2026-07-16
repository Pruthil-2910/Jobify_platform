from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class JobResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    company_name: str
    title: str
    location: str
    description: str
    application_link: str
    employment_type: str
    is_remote: bool
    source: str
    posted_at: datetime
    is_active: Optional[bool] = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    offset: int
    limit: int


    model_config = ConfigDict(from_attributes=True)

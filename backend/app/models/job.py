import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    application_link: Mapped[str] = mapped_column(String(500), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
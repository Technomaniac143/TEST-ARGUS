from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_stage: Mapped[str] = mapped_column(String(80), default="planning")
    total_urls: Mapped[int] = mapped_column(Integer, default=0)
    processed_urls: Mapped[int] = mapped_column(Integer, default=0)
    verified_businesses: Mapped[int] = mapped_column(Integer, default=0)
    discovered_businesses: Mapped[int] = mapped_column(Integer, default=0)
    failed_urls: Mapped[int] = mapped_column(Integer, default=0)
    stage_progress: Mapped[int] = mapped_column(Integer, default=0)
    candidate_urls_json: Mapped[str] = mapped_column(Text, default="[]")
    partial_businesses_json: Mapped[str] = mapped_column(Text, default="[]")
    failed_urls_json: Mapped[str] = mapped_column(Text, default="[]")
    enrichment_status: Mapped[str] = mapped_column(String(80), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    session = relationship("ResearchSession", back_populates="jobs")

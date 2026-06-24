from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    field: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120))
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    normalized_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_type: Mapped[str] = mapped_column(String(120), default="unknown")
    extraction_method: Mapped[str] = mapped_column(String(80), default="regex")
    reliability_score: Mapped[int] = mapped_column(Integer, default=50)
    crawl_status: Mapped[str] = mapped_column(String(40), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    business = relationship("Business", back_populates="evidence")

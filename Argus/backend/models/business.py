from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    dna_score: Mapped[float] = mapped_column(Float, default=0)
    risk: Mapped[str] = mapped_column(String(40), default="UNKNOWN")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session = relationship("ResearchSession", back_populates="businesses")
    evidence = relationship("Evidence", back_populates="business", cascade="all, delete-orphan")
    conflicts = relationship("Conflict", back_populates="business", cascade="all, delete-orphan")

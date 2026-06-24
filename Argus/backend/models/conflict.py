from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Conflict(Base):
    __tablename__ = "conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    field: Mapped[str] = mapped_column(String(120), index=True)
    value1: Mapped[str] = mapped_column(Text)
    value2: Mapped[str] = mapped_column(Text)
    source1: Mapped[str] = mapped_column(String(120))
    source2: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    business = relationship("Business", back_populates="conflicts")

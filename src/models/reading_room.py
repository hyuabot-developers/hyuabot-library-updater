from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import mapped_column, Mapped

from models import BaseModel


class ReadingRoom(BaseModel):
    __tablename__ = "reading_room"
    __table_args__ = (PrimaryKeyConstraint("campus_id", "room_id"),)
    campus_id: Mapped[int] = mapped_column(nullable=False)
    room_id: Mapped[int] = mapped_column(nullable=False)
    room_name: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    is_reservable: Mapped[bool] = mapped_column(nullable=False)
    total: Mapped[int] = mapped_column(nullable=False)
    active_total: Mapped[int] = mapped_column(nullable=False)
    occupied: Mapped[int] = mapped_column(nullable=False)
    available: Mapped[int] = mapped_column(nullable=False)

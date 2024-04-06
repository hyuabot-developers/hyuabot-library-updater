import datetime

from sqlalchemy import String, PrimaryKeyConstraint, ForeignKey, Computed
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseModel(DeclarativeBase):
    pass


class Campus(BaseModel):
    __tablename__ = "campus"
    campus_id: Mapped[int] = mapped_column(primary_key=True)
    campus_name: Mapped[str] = mapped_column(String(30))
    reading_rooms: Mapped["ReadingRoom"] = relationship(back_populates="campus")


class ReadingRoom(BaseModel):
    __tablename__ = "reading_room"
    __table_args__ = (PrimaryKeyConstraint("campus_id", "room_id"),)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campus.campus_id"), nullable=False)
    room_id: Mapped[int] = mapped_column(nullable=False)
    room_name: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    is_reservable: Mapped[bool] = mapped_column(nullable=False)
    total: Mapped[int] = mapped_column(nullable=False)
    active_total: Mapped[int] = mapped_column(nullable=False)
    occupied: Mapped[int] = mapped_column(nullable=False)
    available: Mapped[int] = mapped_column(
        Computed("total - occupied", persisted=True),
        nullable=False,
    )
    last_updated_time: Mapped[datetime.datetime] = \
        mapped_column(nullable=False)
    campus: Mapped["Campus"] = relationship(back_populates="reading_rooms")

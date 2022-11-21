from sqlalchemy import PrimaryKeyConstraint, Column
from sqlalchemy.sql import sqltypes

from models import BaseModel


class ReadingRoom(BaseModel):
    __tablename__ = "reading_room"
    __table_args__ = (PrimaryKeyConstraint("campus_id", "room_id"),)
    campus_id = Column(sqltypes.Integer, nullable=False)
    room_id = Column(sqltypes.Integer, nullable=False)
    room_name = Column(sqltypes.String, nullable=False)
    is_active = Column(sqltypes.Boolean, nullable=False)
    is_reservable = Column(sqltypes.Boolean, nullable=False)
    total = Column(sqltypes.Integer, nullable=False)
    active_total = Column(sqltypes.Integer, nullable=False)
    occupied = Column(sqltypes.Integer, nullable=False)
    available = Column(sqltypes.Integer, nullable=False)

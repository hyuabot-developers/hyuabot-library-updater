from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models import BaseModel


class Campus(BaseModel):
    __tablename__ = "campus"
    campus_id: Mapped[int] = mapped_column(primary_key=True)
    campus_name: Mapped[str] = mapped_column(String(30))

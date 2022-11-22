import pytest as pytest
from sqlalchemy import Engine, insert
from sqlalchemy.orm import sessionmaker, Session

from models import Campus, ReadingRoom
from scripts.realtime import get_realtime_data
from utils.database import get_db_engine


class TestFetchReadingRoomData:
    connection: Engine = None
    session_constructor = None
    session: Session = None

    @classmethod
    async def setup_class(cls):
        cls.connection = await get_db_engine()
        cls.session_constructor = sessionmaker(bind=cls.connection)
        # Database session check
        cls.session = cls.session_constructor()
        assert cls.session is not None
        # Insert campus data
        cls.session.execute(insert(Campus), [
            dict(campus_id=1, campus_name="서울"), dict(campus_id=2, campus_name="ERICA")])
        cls.session.commit()
        cls.session.close()

    @pytest.mark.asyncio
    async def test_fetch_realtime_data(self):
        connection = await get_db_engine()
        session_constructor = sessionmaker(bind=connection)
        # Database session check
        session = session_constructor()
        await get_realtime_data(session)
        # Check if the data is inserted
        room_query = session.query(ReadingRoom).all()
        for room in room_query:  # type: ReadingRoom
            assert room.campus_id == 1 or room.campus_id == 2
            assert type(room.room_id) == int
            assert type(room.room_name) == str
            assert type(room.is_active) == bool
            assert type(room.is_reservable) == bool
            assert type(room.total) == int
            assert type(room.active_total) == int
            assert type(room.occupied) == int
            assert type(room.available) == int

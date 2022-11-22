import pytest as pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert

from models import Campus, ReadingRoom, BaseModel
from scripts.realtime import get_realtime_data
from utils.database import get_db_engine


class TestFetchReadingRoomData:
    connection: Engine | None = None
    session_constructor = None
    session: Session | None = None

    @classmethod
    def setup_class(cls):
        cls.connection = get_db_engine()
        cls.session_constructor = sessionmaker(bind=cls.connection)
        # Database session check
        cls.session = cls.session_constructor()
        assert cls.session is not None
        # Migration schema check
        BaseModel.metadata.create_all(cls.connection)
        # Insert campus data
        insert_statement = insert(Campus).values([
            dict(campus_id=1, campus_name="서울"), dict(campus_id=2, campus_name="ERICA")
        ])
        insert_statement = insert_statement.on_conflict_do_update(
            index_elements=["campus_id"],
            set_=dict(campus_name=insert_statement.excluded.campus_name),
        )
        cls.session.execute(insert_statement)
        cls.session.commit()
        cls.session.close()

    @pytest.mark.asyncio
    async def test_fetch_realtime_data(self):
        connection = get_db_engine()
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

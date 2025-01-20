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
            dict(campus_id=1, campus_name="서울"), dict(campus_id=2, campus_name="ERICA"),
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
        url_list = [
            "https://library.hanyang.ac.kr/pyxis-api/1/seat-rooms?smufMethodCode=PC&branchGroupId=1",
            "https://library.hanyang.ac.kr/pyxis-api/2/seat-rooms?smufMethodCode=PC&branchGroupId=2",
        ]
        for url in url_list:
            await get_realtime_data(session, url)
        # Check if the data is inserted
        room_query = session.query(ReadingRoom).all()
        for room in room_query:  # type: ReadingRoom
            assert room.campus_id == 1 or room.campus_id == 2
            assert isinstance(room.room_id, int)
            assert isinstance(room.room_name, str)
            assert isinstance(room.is_active, bool)
            assert isinstance(room.is_reservable, bool)
            assert isinstance(room.total, int)
            assert isinstance(room.active_total, int)
            assert isinstance(room.occupied, int)
            assert isinstance(room.available, int)

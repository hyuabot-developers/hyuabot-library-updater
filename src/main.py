import asyncio

from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from models import ReadingRoom
from scripts.realtime import get_realtime_data, get_branches
from utils.database import get_db_engine


async def main():
    connection = get_db_engine()
    session_constructor = sessionmaker(bind=connection)
    session = session_constructor()
    if session is None:
        raise RuntimeError("Failed to get db session")
    await execute_script(session)


async def execute_script(session):
    branches = await get_branches()
    campus_list = set(branches.values())
    job_list = [get_realtime_data(session, campus_id) for campus_id in campus_list]
    session.execute(delete(ReadingRoom))
    await asyncio.gather(*job_list)
    session.close()

if __name__ == '__main__':
    asyncio.run(main())

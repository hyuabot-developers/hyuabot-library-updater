from aiohttp import ClientTimeout, ClientSession
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from models.reading_room import ReadingRoom


async def get_realtime_data(db_session: Session) -> None:
    url = f"https://lib.hanyang.ac.kr/smufu-api/pc/0/rooms-at-seat"
    timeout = ClientTimeout(total=3.0)
    room_items: list[dict] = []
    async with ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response_json = await response.json()
            room_list = response_json["data"]["list"]
            for room in room_list:
                room_items.append(dict(
                    campus_id=room["branchGroup"]["id"],
                    room_id=room["id"],
                    room_name=room["name"],
                    is_active=room["isActive"],
                    is_reservable=room["isReservable"],
                    total=room["total"],
                    active_total=room["activeTotal"],
                    occupied=room["occupied"],
                    available=room["available"],
                ))
    db_session.execute(delete(ReadingRoom))
    if room_items:
        insert_statement = insert(ReadingRoom).values(room_items)
        db_session.execute(insert_statement)
    db_session.commit()

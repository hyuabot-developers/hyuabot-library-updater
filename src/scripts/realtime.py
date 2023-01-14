from aiohttp import ClientTimeout, ClientSession
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from models import ReadingRoom


async def get_realtime_data(db_session: Session) -> None:
    url = "https://lib.hanyang.ac.kr/smufu-api/pc/0/rooms-status"
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
    try:
        db_session.execute(delete(ReadingRoom))
    finally:
        if room_items:
            db_session.execute(insert(ReadingRoom), room_items)
        db_session.commit()

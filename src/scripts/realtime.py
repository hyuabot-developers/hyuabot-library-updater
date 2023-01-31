import os

from aiohttp import ClientTimeout, ClientSession
from pyfcm import FCMNotification
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from models import ReadingRoom

firebase_key = os.getenv("FIREBASE_TOKEN")
push_service = FCMNotification(api_key=firebase_key)


async def get_realtime_data(db_session: Session) -> None:
    url = "https://lib.hanyang.ac.kr/smufu-api/pc/0/rooms-status"
    timeout = ClientTimeout(total=30)
    room_items: list[dict] = []
    async with ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response_json = await response.json()
            room_list = response_json["data"]["list"]
            for room in room_list:
                if room["available"] > 0:
                    data = {
                        "body": f"{room['name']}에 좌석이 {room['available']}개 남았습니다.",
                        "title": "열람실 좌석 발견!",
                    }
                    push_service.notify_topic_subscribers(
                        topic_name=f"reading_room_{room['id']}", data_message=data,
                    )
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

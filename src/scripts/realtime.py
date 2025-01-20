import datetime
import os

from aiohttp import ClientTimeout, ClientSession
from pyfcm import FCMNotification
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from models import ReadingRoom

google_project_id = os.getenv("GOOGLE_PROJECT_ID")
push_service = FCMNotification(
    service_account_file="/tmp/google-service-account.json",
    project_id=google_project_id,
)


async def get_realtime_data(db_session: Session, url: str) -> None:
    timeout = ClientTimeout(total=30)
    room_items: list[dict] = []
    now = datetime.datetime.now()
    async with ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response_json = await response.json()
            room_list = response_json["data"]["list"]
            for room in room_list:
                seats = room["seats"]
                if seats["available"] > 0:
                    data = {
                        "body": f"{room['name']}에 좌석이 {seats['available']}개 남았습니다.",
                        "title": "열람실 좌석 발견!",
                    }
                    push_service.notify(
                        topic_name=f"reading_room_{room['id']}",
                        data_payload=data,
                    )
                room_items.append(dict(
                    campus_id=room["branch"]["id"],
                    room_id=room["id"],
                    room_name=room["name"],
                    is_active=room["unableMessage"] is None,
                    is_reservable=room["unableMessage"] is None,
                    total=seats["total"],
                    active_total=seats["total"],
                    occupied=seats["occupied"],
                    last_updated_time=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))),
                ))
    try:
        db_session.execute(delete(ReadingRoom))
    finally:
        if room_items:
            db_session.execute(insert(ReadingRoom), room_items)
        db_session.commit()

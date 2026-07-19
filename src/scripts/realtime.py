import asyncio
import datetime
import json
import os
from typing import Any

from aiohttp import ClientError, ClientTimeout, ClientSession
from pyfcm import FCMNotification
from sqlalchemy import insert
from sqlalchemy.orm import Session

from models import ReadingRoom

google_project_id = os.getenv("GOOGLE_PROJECT_ID")
push_service = FCMNotification(
    service_account_file="/tmp/google-service-account.json",
    project_id=google_project_id,
)

LIBRARY_API_TIMEOUT_SECONDS = 10
LIBRARY_API_MAX_ATTEMPTS = 3
LIBRARY_API_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def _response_summary(response_text: str, limit: int = 200) -> str:
    summary = " ".join(response_text.split())
    return summary[:limit]


async def _get_json(url: str) -> dict[str, Any]:
    timeout = ClientTimeout(total=LIBRARY_API_TIMEOUT_SECONDS)
    async with ClientSession(timeout=timeout, headers={"Accept": "application/json"}) as session:
        for attempt in range(1, LIBRARY_API_MAX_ATTEMPTS + 1):
            try:
                async with session.get(url) as response:
                    response_text = await response.text()
                    if response.status >= 400:
                        summary = _response_summary(response_text)
                        message = f"Library API returned HTTP {response.status} for {url}"
                        if summary:
                            message = f"{message}: {summary}"
                        if (
                            response.status not in LIBRARY_API_RETRYABLE_STATUSES
                            or attempt == LIBRARY_API_MAX_ATTEMPTS
                        ):
                            raise RuntimeError(message)
                    else:
                        content_type = response.headers.get("Content-Type", "").lower()
                        if "json" not in content_type:
                            raise RuntimeError(
                                f"Library API returned non-JSON content ({content_type or 'unknown'}) for {url}"
                            )
                        try:
                            response_json = json.loads(response_text)
                        except json.JSONDecodeError as error:
                            raise RuntimeError(f"Library API returned invalid JSON for {url}") from error
                        if not isinstance(response_json, dict):
                            raise RuntimeError(f"Library API returned an invalid JSON root for {url}")
                        return response_json
            except (ClientError, TimeoutError) as error:
                if attempt == LIBRARY_API_MAX_ATTEMPTS:
                    raise RuntimeError(
                        f"Library API request failed after {LIBRARY_API_MAX_ATTEMPTS} attempts for {url}: {error}"
                    ) from error

            delay = 2 ** (attempt - 1)
            print(
                f"Library API request attempt {attempt}/{LIBRARY_API_MAX_ATTEMPTS} failed for {url}; "
                f"retrying in {delay}s"
            )
            await asyncio.sleep(delay)

    raise RuntimeError(f"Library API request failed for {url}")


async def get_branches() -> dict[int, int]:
    url = "https://library.hanyang.ac.kr/pyxis-api/1/branches"
    response_json = await _get_json(url)
    branch_list = response_json["data"]["list"]
    return {branch["id"]: branch["branchGroup"]["id"] for branch in branch_list}


async def get_realtime_data(db_session: Session, campus_id: int) -> None:
    room_items: list[dict] = []
    now = datetime.datetime.now()
    url = f"https://library.hanyang.ac.kr/pyxis-api/{campus_id}/seat-rooms?smufMethodCode=PC&branchGroupId={campus_id}"
    response_json = await _get_json(url)
    if response_json.get("data") is None:
        return
    room_list = response_json["data"]["list"]
    for room in room_list:
        seats = room["seats"]
        if seats["available"] > 0:
            data = {
                "body": f"{room['name']}에 좌석이 {seats['available']}개 남았습니다.",
                "title": "열람실 좌석 발견!",
                "id": f'reading_room_{room["id"]}',
                "available": str(seats['total'] - seats['occupied']),
            }
            push_service.notify(
                topic_name=f"reading_room_{room['id']}",
                data_payload=data,
            )
        room_items.append(dict(
            campus_id=campus_id,
            room_id=room["id"],
            room_name=room["name"],
            is_active=True,
            is_reservable=room["unableMessage"] is None,
            total=seats["total"],
            active_total=seats["total"],
            occupied=seats["occupied"],
            last_updated_time=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))),
        ))
    if room_items:
        db_session.execute(insert(ReadingRoom), room_items)
    db_session.commit()

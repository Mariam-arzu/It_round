import json
import os
from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel

from .database import Event


def format_events(events: List[Event]) -> str:
    if not events:
        return "No events scheduled"
    return "\n".join(
        f"{i+1}. {e.event_name} - {e.event_date.strftime('%Y-%m-%d %H:%M')}"
        for i, e in enumerate(events)
    )


def get_time_range(period: str) -> tuple:
    now = datetime.now()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "tomorrow":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
        end = start + timedelta(days=1)
    elif period == "week":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(weeks=1)
    return start, end


class ScheduleItem(BaseModel):
    lesson: str
    time: str


with open(os.path.join("app", "schedule.json"), "r", encoding="utf-8") as file:
    schedule = json.load(file)

schedule: dict[str, list[ScheduleItem]] = {
    key: [ScheduleItem(**t) for t in item] for key, item in schedule.items()
}

weekday_map = {
    "0": "Понедельник",
    "1": "Вторник",
    "2": "Среда",
    "3": "Четверг",
    "4": "Пятница",
    "5": "Суббота",
}


def get_schedule(date, day: str) -> str | None:
    weekday = weekday_map.get(day)
    if weekday:
        text = "\n".join(
            [
                f"  {idx + 1}. {item.lesson}\t{item.time}"
                for idx, item in enumerate(schedule[day])
            ]
        )
        return f"Расписание на {date} [{weekday}]:\n\n" + text + "\n"
    return None

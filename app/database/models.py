from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class EventCreate(BaseModel):
    event_name: str
    event_date: datetime

    @field_validator("event_date")
    def parse_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        return value


class EventResponse(BaseModel):
    event_name: str
    event_day: str
    event_time: str


class EventNotofication(BaseModel):
    event_id: int
    chat_id: str
    event_name: str
    event_date: datetime

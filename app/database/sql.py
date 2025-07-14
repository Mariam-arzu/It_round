from datetime import datetime, timedelta
from functools import wraps
from typing import Literal

from .base import AccountData, Event, Session, db
from .models import EventCreate, EventNotofication, EventResponse


def handle_db_query(func):
    """
    A decorator to handle database session commit and rollback in case of exceptions.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        with db.get_session() as session:
            try:
                result = func(session=session, *args, **kwargs)
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                raise e

    return wrapper


class SQLDataBase:
    def __init__(self):
        pass

    @handle_db_query
    def get_events(self, start, end, session: Session) -> list[EventNotofication]:
        query = (
            session.query(Event)
            .filter(
                Event.event_date >= start,
                Event.event_date <= end,
                Event.notified == False,
            )
            .order_by(Event.event_date)
            .all()
        )
        if query:
            return [
                EventNotofication(
                    event_id=event.id,
                    chat_id=event.user_id,
                    event_name=event.event_name,
                    event_date=event.event_date,
                )
                for event in query
            ]
        return []

    @handle_db_query
    def set_event_state(self, event_id: int, session: Session) -> None:
        event = session.query(Event).filter(Event.id == event_id)
        event.update({Event.notified: True})

    @handle_db_query
    def get_user_events(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        session: Session = None,
    ) -> list[EventResponse]:
        query = (
            session.query(Event)
            .filter(
                Event.user_id == user_id,
                Event.event_date >= start,
                Event.event_date < end,
            )
            .order_by(Event.event_date)
            .all()
        )
        if query:
            return [
                EventResponse(
                    event_name=_q.event_name,
                    event_day=f"{_q.event_date.day}.{_q.event_date.month}",
                    event_time=f"{_q.event_date.hour}:{_q.event_date.minute}",
                )
                for _q in query
            ]
        return []

    @handle_db_query
    def add_event(self, user_id: str, event: EventCreate, session: Session = None):
        db_event = Event(
            user_id=user_id,
            event_name=event.event_name,
            event_date=event.event_date,
        )
        session.add(db_event)

    @handle_db_query
    def get_notification(self, session: Session):
        pass

    @handle_db_query
    def add_account(self, user_id: str, session: Session = None):
        new_account = AccountData(chat_id=user_id)
        session.add(new_account)

    @handle_db_query
    def account_exists(self, user_id: str, session: Session = None):
        account = (
            session.query(AccountData)
            .filter(AccountData.chat_id == user_id)
            .one_or_none()
        )
        if account:
            return True
        return False

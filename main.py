#### settings

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.orm.decl_api import registry
from sqlalchemy_utils import create_database, database_exists

api_key = "7628846836:AAFuRBCFG9mw5zAsvGGGg6-6wgtfVHL-xrI"

### DATABASE


mapper_registry = registry()
metadata = mapper_registry.metadata


Base = declarative_base(metadata=metadata)


# Tables


class AccountData(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Text, nullable=True, unique=True)


class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(Text, nullable=False)
    event_date = Column(DateTime, nullable=False)
    user_id = Column(Text, ForeignKey("account.chat_id"))
    user = relationship("AccountData")
    notified = Column(Boolean, nullable=False, default=False)


# init


def get_db_config(
    database: str = "chatter.db",
    driver: str = "sqlite",
):
    db_config = f"{driver}:///{database}.db"
    return db_config


class SQLAlchemy:
    """
    Обертка вокруг engine и session для удобства подмены тестов и обобщения
    """

    def __init__(self):
        db_config = get_db_config()
        self.engine = create_engine(db_config)

        if not database_exists(self.engine.url):
            create_database(self.engine.url)
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)

        # TODO initialize a database
        pass

    def get_session(self, **kwargs) -> Session:
        """
        db = SQLAlchemy()
        with db.get_session() as session:
            do_some_stuff

        """
        _Session = sessionmaker(bind=self.engine)
        return _Session(**kwargs)


db = SQLAlchemy()


#### MODELS

from datetime import datetime, timedelta

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


### SQL Manipulation


from datetime import datetime, timedelta
from functools import wraps


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


###### telebot

import json
from typing import List


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


import os

schedule = {
    "0": [
        {"lesson": "Алгебра", "time": "9:00 - 9:45"},
        {"lesson": "Физика", "time": "9:50 - 10:35"},
        {"lesson": "Химия", "time": "10:40 - 11:25"},
        {"lesson": "История", "time": "11:30 - 12:15"},
        {"lesson": "Геометрия", "time": "13:15 - 14:00"},
    ],
    "1": [
        {"lesson": "Физика", "time": "9:00 - 9:45"},
        {"lesson": "Алгебра", "time": "9:50 - 10:35"},
        {"lesson": "Биология", "time": "10:40 - 11:25"},
        {"lesson": "Физкультура", "time": "11:30 - 12:15"},
        {"lesson": "Геометрия", "time": "13:15 - 14:00"},
    ],
    "2": [
        {"lesson": "Алгебра", "time": "9:00 - 9:45"},
        {"lesson": "Физика", "time": "9:50 - 10:35"},
        {"lesson": "Химия", "time": "10:40 - 11:25"},
        {"lesson": "Русский язык", "time": "11:30 - 12:15"},
        {"lesson": "Английский язык", "time": "13:15 - 14:00"},
    ],
    "3": [
        {"lesson": "Химия", "time": "9:00 - 9:45"},
        {"lesson": "Русский язык", "time": "9:50 - 10:35"},
        {"lesson": "Литература", "time": "10:40 - 11:25"},
        {"lesson": "История", "time": "11:30 - 12:15"},
        {"lesson": "География", "time": "13:15 - 14:00"},
    ],
    "4": [
        {"lesson": "Алгебра", "time": "9:00 - 9:45"},
        {"lesson": "Физика", "time": "9:50 - 10:35"},
        {"lesson": "ОБЖ", "time": "10:40 - 11:25"},
        {"lesson": "Биология", "time": "11:30 - 12:15"},
        {"lesson": "Информатика", "time": "13:15 - 14:00"},
    ],
    "5": [
        {"lesson": "Геометрия", "time": "9:00 - 9:45"},
        {"lesson": "Алгебра", "time": "9:50 - 10:35"},
        {"lesson": "Химия", "time": "10:40 - 11:25"},
        {"lesson": "Информатика", "time": "11:30 - 12:15"},
        {"lesson": "Литература", "time": "13:15 - 14:00"},
    ],
}

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


import logging
from functools import wraps

logging.basicConfig(level=logging.INFO, filename="log.log")

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, KeyboardButton, ReplyKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, filename="")

bot = Bot(token=api_key)
dp = Dispatcher()
database = SQLDataBase()

KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/today"),
            KeyboardButton(text="/tomorrow"),
            KeyboardButton(text="/week"),
        ],
        [
            KeyboardButton(text="/add"),
            KeyboardButton(text="/schedule"),
            KeyboardButton(text="/help"),
        ],
    ],
    resize_keyboard=True,  # Make buttons smaller
    one_time_keyboard=False,  # Persistent keyboard
    is_persistent=True,  # Persistent like BotFather menu
)


class SendComment(StatesGroup):
    comment = State()


class EventStates(StatesGroup):
    waiting_for_event_name = State()
    waiting_for_event_date = State()


scheduler = AsyncIOScheduler()


def check_user(message: types.Message):
    if not database.account_exists(user_id=str(message.chat.id)):
        database.add_account(user_id=str(message.chat.id))


@dp.message(Command(commands=["start", "help"]))
async def send_welcome(message: types.Message):
    check_user(message)

    help_text = (
        "Добро пожаловать в чат-бот для расписаний!\n\n"
        "Доступные команды:\n"
        "/today - расписание сегодня\n"
        "/tomorrow - расписание завтра\n"
        "/week - расписание на неделю\n"
        "/add - добавить событие\n"
        "/schedule - как добавлять события\n"
        "/help - общая информация"
    )
    await message.reply(help_text, reply_markup=KEYBOARD)
    # check for events
    # await check_events()


@dp.message(Command(commands=["schedule"]))
async def schedule_info(message: types.Message):
    check_user(message)

    info_text = (
        "Чтобы добавить событие используйте форму:\n"
        "/add Наименование YYYY-MM-DD HH:MM\n\n"
        "Пример:\n"
        "/add Контрольная 2025-07-10 14:30"
    )
    await message.reply(info_text, reply_markup=KEYBOARD)
    # check for events
    # await check_events()


@dp.message(Command(commands=["today", "tomorrow", "week"]))
async def show_schedule(message: types.Message):
    check_user(message)

    period = message.text[1:]  # Remove leading '/'
    start, end = get_time_range(period)
    events = []

    if message.text[1:] == "today":
        schedule = get_schedule(datetime.strftime(start, "%d.%m"), str(start.weekday()))
        if start.weekday() == 6:
            schedule = "В воскресенье не учимся)\n"

        events = database.get_user_events(str(message.chat.id), start, end)

    elif message.text[1:] == "tomorrow":
        schedule = get_schedule(datetime.strftime(start, "%d.%m"), str(start.weekday()))
        if start.weekday() == 6:
            schedule = "В воскресенье не учимся)\n"

        events = database.get_user_events(str(message.chat.id), start, end)

    elif message.text[1:] == "week":
        schedule = []
        while start < end:
            if start.weekday() == 6:
                schedule.append(
                    f"В воскресенье {datetime.strftime(start, "%d.%m")} не учимся)\n"
                )
            else:
                schedule.append(
                    get_schedule(
                        datetime.strftime(start, "%d.%m"), str(start.weekday())
                    )
                )

            events = database.get_user_events(
                str(message.chat.id), start, start + timedelta(days=1)
            )

            if events:
                schedule[-1] += (
                    f"\nСобытия на {datetime.strftime(start, "%d.%m")}\n\n"
                    + "\n".join(
                        [
                            f"\t{idx + 1}. {event.event_name} в {event.event_time}"
                            for idx, event in enumerate(events)
                        ]
                    )
                    + "\n"
                )

            start += timedelta(days=1)

        schedule = "\n".join(schedule)

    # response = f"{period.capitalize()} schedule:\n{format_events(events)}"
    response = ""
    if schedule:
        response += schedule
    if events and message.text[1:] != "week":
        response += f"\n События на {period.capitalize()}\n\n" + "\n".join(
            [
                f"\t{idx + 1}. {event.event_name} в {event.event_time}"
                for idx, event in enumerate(events)
            ]
        )
    await message.reply(response)
    # check for events
    # await check_events()


@dp.message(Command(commands=["add"]))
async def add_event_start(message: types.Message):
    args = message.text.replace("/add", "").strip().split(maxsplit=1)
    if len(args) >= 2:
        try:
            event_name, date_str = args
            event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            event = EventCreate(event_name=event_name, event_date=event_date)

            database.add_event(str(message.chat.id), event)

            await message.reply(f"Event added: {event_name} at {date_str}")
        except ValueError:
            await message.reply(
                "Invalid date format. Use: /add event_name YYYY-MM-DD HH:MM"
            )
    else:
        await message.reply(
            "Please provide event name and date\nExample: /add Meeting 2023-12-20 15:00"
        )
    # check for events
    # await check_events()


async def check_events():
    now = datetime.now()
    end = now + timedelta(hours=1)

    events = database.get_events(start=now, end=end)

    for event in events:
        try:
            time_left = event.event_date - now
            minutes = int(time_left.total_seconds() // 60)
            await bot.send_message(
                event.chat_id,
                f"⏰ Напоминание: {event.event_name} начнется через {minutes} минут в {event.event_date.time()}!",
            )
            database.set_event_state(event.event_id)
        except Exception as e:
            logging.log(level=logging.ERROR, msg=f"{e}")


# Глобальный обработчик ошибок
@dp.errors()
async def global_error_handler(update, error):
    try:
        raise error

    except Exception as e:
        logging.info(f"error: {e}")
        logging.info(f"Неожиданная ошибка: {e}")

    return True  # Чтобы ошибки не прерывали работу бота


async def on_startup():
    # Define commands for the drop-down menu
    commands = [
        BotCommand(command="today", description=""),
        BotCommand(command="tomorrow", description=""),
        BotCommand(command="week", description=""),
        BotCommand(command="add", description=""),
        BotCommand(command="schedule", description=""),
        BotCommand(command="help", description=""),
    ]
    await bot.set_my_commands(commands)

    # Set the default menu button to display commands
    await bot.set_menu_button()


async def main():

    # Start scheduler for notifications
    scheduler.add_job(check_events, "interval", minutes=1)
    scheduler.start()

    # запускаем бота
    await dp.start_polling(bot, on_startup=on_startup)


if __name__ == "__main__":

    import asyncio

    asyncio.run(main())

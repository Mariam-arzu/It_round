import logging
from functools import wraps

logging.basicConfig(level=logging.INFO, filename="log.log")
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, KeyboardButton, ReplyKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import get_database
from .helper import format_events, get_schedule, get_time_range

logging.basicConfig(level=logging.INFO, filename="")
from .core import get_api_token
from .database import EventCreate, get_database

bot = Bot(token=get_api_token())
dp = Dispatcher()
database = get_database()

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

    match message.text[1:]:
        case "today":
            schedule = get_schedule(
                datetime.strftime(start, "%d.%m"), str(start.weekday())
            )
            if start.weekday() == 6:
                schedule = "В воскресенье не учимся)\n"

        case "tomorrow":
            schedule = get_schedule(
                datetime.strftime(start, "%d.%m"), str(start.weekday())
            )
            if start.weekday() == 6:
                schedule = "В воскресенье не учимся)\n"

        case "week":
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
                start += timedelta(days=1)

            schedule = "\n".join(schedule)

    events = database.get_user_events(str(message.chat.id), start, end)

    # response = f"{period.capitalize()} schedule:\n{format_events(events)}"
    response = ""
    if schedule:
        response += schedule
    if events:
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

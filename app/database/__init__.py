from .base import Event
from .models import EventCreate
from .sql import SQLDataBase


def get_database() -> SQLDataBase:
    return SQLDataBase()


__all__ = ["EventCreate", "Event"]

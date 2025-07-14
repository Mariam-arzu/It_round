import enum

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

from app.core import config

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
    database: str = config.DATABASE_NAME,
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

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    REDIS_PORT: int = 6379
    REDIS_HOST: str = "localhost"

    DATABASE_NAME: str = "chatter"

    SERIALIZER: str = "redis"
    INTERFACE: str = "telegram"

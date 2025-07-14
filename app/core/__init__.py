from .settings import AppSettings


def get_settings() -> AppSettings:

    return AppSettings()


config = get_settings()

match config.INTERFACE:
    case "telegram":
        from .keys import api_key

        def get_api_token() -> str:
            return api_key

    case "gradio":
        pass

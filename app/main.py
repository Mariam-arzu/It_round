import asyncio

from .core import config
from .gradio import gradio_app
from .telebot import bot, check_events, dp, on_startup, scheduler


async def main():

    # Start scheduler for notifications
    scheduler.add_job(check_events, "interval", minutes=1)
    scheduler.start()

    # demo.launch(server_name="0.0.0.0", server_port=7860)
    # await run()

    # return

    if config.INTERFACE == "telegram":
        # asyncio.create_task(
        await dp.start_polling(bot, on_startup=on_startup)
    # )
    # asyncio.c

    elif config.INTERFACE == "gradio":
        # gradio_app.launch(server_name="0.0.0.0", server_port=7860)
        import threading

        def run_gradio_app():
            gradio_app.launch(server_name="0.0.0.0", server_port=7860)

        gradio_thread = threading.Thread(target=run_gradio_app, daemon=True)
        gradio_thread.start()
    else:
        raise ValueError("Нужно указать интерфейс!")


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(dp.start_polling(bot, on_startup=on_startup))

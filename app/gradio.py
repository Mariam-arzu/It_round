from datetime import datetime, timedelta

import gradio as gr

from .database import Event, EventCreate, get_database
from .helper import get_schedule, get_time_range

database = get_database()


def gradio_add_event(user_id: str, event_name: str, event_date: str):
    try:
        event_date_dt = datetime.strptime(event_date, "%Y-%m-%d %H:%M")
        event = EventCreate(event_name=event_name, event_date=event_date_dt)

        database.add_event(user_id=user_id, event=event)

        return f"Event added: {event_name} at {event_date}"
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD HH:MM"


def gradio_get_schedule(user_id: str, period: str):
    start, end = get_time_range(period)

    events = database.get_events(start=start, end=end)

    if not events:
        return [], "No events found"

    event_data = [
        [e.event_name, e.event_date.strftime("%Y-%m-%d %H:%M")] for e in events
    ]
    return event_data, f"Found {len(events)} events"


with gr.Blocks(title="Student Schedule Manager") as gradio_app:
    gr.Markdown("# Student Schedule Manager")

    with gr.Tab("View Schedule"):
        user_id_input = gr.Textbox(label="User ID")
        period_input = gr.Dropdown(
            label="Period", choices=["today", "tomorrow", "week"], value="today"
        )
        view_button = gr.Button("View Schedule")
        schedule_output = gr.Dataframe(headers=["Event", "Date"], label="Schedule")
        status_output = gr.Textbox(label="Status")
        view_button.click(
            fn=gradio_get_schedule,
            inputs=[user_id_input, period_input],
            outputs=[schedule_output, status_output],
        )

    with gr.Tab("Add Event"):
        add_user_id_input = gr.Textbox(label="User ID")
        event_name_input = gr.Textbox(label="Event Name")
        event_date_input = gr.Textbox(
            label="Event Date (YYYY-MM-DD HH:MM)", placeholder="2023-12-31 14:30"
        )
        add_button = gr.Button("Add Event")
        add_result_output = gr.Textbox(label="Result")
        add_button.click(
            fn=gradio_add_event,
            inputs=[add_user_id_input, event_name_input, event_date_input],
            outputs=add_result_output,
        )

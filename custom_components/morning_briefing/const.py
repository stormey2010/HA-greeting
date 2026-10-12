"""Constants for Parker's morning briefing integration."""

from datetime import timedelta

DOMAIN = "morning_briefing"
PLATFORMS = ["sensor"]
SERVICE_GENERATE = "generate"
CONF_CEREBRAS_API_KEY = "cerebras_api_key"
CONF_CEREBRAS_MODEL = "cerebras_model"
CONF_GMAIL_ENABLED = "gmail_enabled"
CONF_GMAIL_RECONNECT = "gmail_reconnect"
CONF_CALDAV_URL = "caldav_url"
CONF_CALDAV_USER = "caldav_username"
CONF_CALDAV_PASSWORD = "caldav_password"
CONF_CALENDAR_NAMES = "calendar_names"
DEFAULT_CALDAV_URL = "https://caldav.icloud.com"
DEFAULT_MODEL = "gpt-oss-120b"
DEFAULT_OPTIONS = {
    "weather_enabled": True,
    "weather_entity": "weather.forecast_home",
    "calendar_enabled": True,
    "calendar_source": "caldav",
    "calendar_entities": [],
    "calendar_names": [],
    "calendar_labels": "",
    "todo_enabled": True,
    "todo_entities": [],
    "presence_enabled": False,
    "presence_entities": [],
    "batteries_enabled": False,
    "battery_entities": [],
    "low_battery_percent": 25,
    "max_calendar_events": 8,
    "max_todo_items": 4,
    "max_gmail_messages": 4,
    "speaker_script": "script.new_script",
    "speaker_entity": "media_player.parker_s_echo_dot",
    "speaker_volume": 29,
    "gmail_enabled": False,
}
UPDATE_INTERVAL = timedelta(minutes=1)

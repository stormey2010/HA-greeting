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
DEFAULT_BRIEFING_PROMPT = (
    "Write a short, flowing spoken morning briefing that is easy for text-to-speech. "
    "Cover today and tomorrow in natural language. Use supplied calendar labels when "
    "they clearly identify a person or category, and never infer who an event belongs "
    "to from its title. Say times naturally and group calendar items by day. For Gmail, "
    "prioritize important or starred messages, then judge remaining reviewed messages "
    "from their content. Briefly report the approximate unread count and how many "
    "filtered category messages were excluded; summarize only genuinely important "
    "messages, skip routine mail, and never read a message verbatim. If nothing is "
    "important, say so briefly. Use only supplied facts; skip missing data and never invent."
)
GMAIL_CATEGORIES = ["promotions", "social", "forums", "updates"]
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
    "gmail_max_chars": 2500,
    "gmail_excluded_categories": ["promotions", "social", "forums"],
    "cerebras_model": DEFAULT_MODEL,
    "ai_temperature": 0.2,
    "briefing_prompt": DEFAULT_BRIEFING_PROMPT,
    "speaker_script": "script.new_script",
    "speaker_entity": "media_player.parker_s_echo_dot",
    "speaker_volume": 29,
    "gmail_enabled": False,
}
UPDATE_INTERVAL = timedelta(minutes=1)

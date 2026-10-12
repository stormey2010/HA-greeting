"""Editable text and list settings for the briefing."""

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_OPTIONS
from .settings_common import device_info, save_option


TEXT_SETTINGS = (
    ("briefing_prompt_override", "AI prompt additions (255 characters)", False, 255),
    ("calendar_labels", "Calendar labels (semicolon separated)", False, 255),
    ("weather_entity", "Weather entity ID", False, 255),
    ("calendar_entities", "Calendar entity IDs (comma separated)", True, 255),
    ("calendar_names", "CalDAV calendar names (comma separated)", True, 255),
    ("todo_entities", "To-do entity IDs (comma separated)", True, 255),
    ("presence_entities", "Person entity IDs (comma separated)", True, 255),
    ("battery_entities", "Battery entity IDs (comma separated)", True, 255),
    ("speaker_script", "Announcement script entity ID", False, 255),
    ("speaker_entity", "Speaker entity ID", False, 255),
    ("gmail_excluded_categories", "Gmail categories to exclude (comma separated)", True, 100),
    ("caldav_url", "CalDAV server URL", False, 255),
    ("caldav_username", "CalDAV account username", False, 255),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up text controls."""
    async_add_entities(
        BriefingText(entry, key, name, is_list, maximum)
        for key, name, is_list, maximum in TEXT_SETTINGS
    )


class BriefingText(TextEntity):
    """A text input persisted directly to one config option."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0

    def __init__(
        self, entry: ConfigEntry, key: str, name: str, is_list: bool, maximum: int
    ) -> None:
        self._entry = entry
        self._key = key
        self._is_list = is_list
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info(entry)
        self._attr_native_max = maximum

    @property
    def native_value(self) -> str:
        """Return the saved value, with list values shown one per line."""
        options = {**DEFAULT_OPTIONS, **self._entry.options}
        if self._key.startswith("caldav_"):
            caldav_key = "url" if self._key == "caldav_url" else "username"
            value = (self._entry.options.get("caldav") or {}).get(caldav_key, "")
        else:
            value = options.get(self._key, "")
        if self._is_list:
            return ", ".join(str(item) for item in value or [])
        return str(value or "")

    async def async_set_value(self, value: str) -> None:
        """Save text or parse a newline-separated list."""
        saved: str | list[str] = value
        if self._is_list:
            saved = [item.strip() for item in value.split(",") if item.strip()]
        if self._key == "calendar_labels":
            saved = "\n".join(item.strip() for item in value.split(";") if item.strip())
        if self._key == "gmail_excluded_categories":
            allowed = {"promotions", "social", "forums", "updates"}
            saved = [item.lower() for item in saved if item.lower() in allowed]
        if self._key.startswith("caldav_"):
            caldav_key = "url" if self._key == "caldav_url" else "username"
            caldav = dict(self._entry.options.get("caldav") or {})
            caldav[caldav_key] = saved
            await save_option(self.hass, self._entry, "caldav", caldav)
        else:
            await save_option(self.hass, self._entry, self._key, saved)
        self.async_write_ha_state()

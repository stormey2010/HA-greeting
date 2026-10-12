"""Editable numeric settings for Parker's Morning Briefing."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_OPTIONS
from .settings_common import device_info, save_option


SETTINGS = (
    ("low_battery_percent", "Low battery threshold", 1, 100, 1, True),
    ("max_calendar_events", "Maximum calendar events", 1, 30, 1, True),
    ("max_todo_items", "Maximum to-do items", 1, 20, 1, True),
    ("max_gmail_messages", "Gmail messages to review", 1, 20, 1, True),
    ("gmail_lookback_days", "Gmail lookback days", 1, 14, 1, True),
    ("gmail_max_chars", "Gmail excerpt size", 250, 10000, 250, True),
    ("speaker_volume", "Announcement volume", 0, 100, 1, True),
    ("ai_temperature", "AI creativity", 0, 1, 0.1, False),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up numeric controls."""
    async_add_entities(
        BriefingNumber(entry, *setting) for setting in SETTINGS
    )


class BriefingNumber(NumberEntity):
    """A number control persisted directly to one config option."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        entry: ConfigEntry,
        key: str,
        name: str,
        minimum: float,
        maximum: float,
        step: float,
        integer: bool,
    ) -> None:
        self._entry = entry
        self._key = key
        self._integer = integer
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info(entry)
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step

    @property
    def native_value(self) -> float:
        """Return the saved setting."""
        options = {**DEFAULT_OPTIONS, **self._entry.options}
        return float(options[self._key])

    async def async_set_native_value(self, value: float) -> None:
        """Save a changed number."""
        saved: int | float = int(value) if self._integer else float(value)
        await save_option(self.hass, self._entry, self._key, saved)
        self.async_write_ha_state()

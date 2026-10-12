"""Editable include/skip switches for briefing sources."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_OPTIONS
from .settings_common import device_info, save_option


SETTINGS = (
    ("weather_enabled", "Include weather"),
    ("calendar_enabled", "Include calendar"),
    ("todo_enabled", "Include to-do items"),
    ("presence_enabled", "Include presence"),
    ("batteries_enabled", "Include low batteries"),
    ("gmail_enabled", "Include Gmail"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up source switches."""
    async_add_entities(BriefingSwitch(entry, key, name) for key, name in SETTINGS)


class BriefingSwitch(SwitchEntity):
    """A source enable/disable setting."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, key: str, name: str) -> None:
        self._entry = entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info(entry)

    @property
    def is_on(self) -> bool:
        """Return whether this source is included."""
        options = {**DEFAULT_OPTIONS, **self._entry.options}
        return bool(options[self._key])

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable this source."""
        await self._set(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable this source."""
        await self._set(False)

    async def _set(self, value: bool) -> None:
        await save_option(self.hass, self._entry, self._key, value)
        self.async_write_ha_state()

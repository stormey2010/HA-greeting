"""Editable choice settings for the briefing."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_MODEL
from .settings_common import device_info, save_option


SETTINGS = (
    ("cerebras_model", "Cerebras model", ["gpt-oss-120b", "qwen-3-32b", "llama3.1-8b"]),
    ("calendar_source", "Calendar source", ["caldav", "home_assistant"]),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select controls."""
    async_add_entities(BriefingSelect(entry, *setting) for setting in SETTINGS)


class BriefingSelect(SelectEntity):
    """A select control persisted directly to one config option."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, key: str, name: str, options: list[str]) -> None:
        self._entry = entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info(entry)
        self._attr_options = options

    @property
    def current_option(self) -> str:
        """Return the saved selection."""
        if self._key == "cerebras_model":
            value = self._entry.options.get(self._key) or self._entry.data.get("cerebras_model", DEFAULT_MODEL)
        else:
            value = self._entry.options.get(self._key, "caldav")
        return str(value)

    async def async_select_option(self, option: str) -> None:
        """Save the selected option."""
        if option not in self.options:
            return
        await save_option(self.hass, self._entry, self._key, option)
        self.async_write_ha_state()

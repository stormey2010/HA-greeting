"""Helpers shared by the integration's editable settings entities."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def device_info(entry: ConfigEntry) -> DeviceInfo:
    """Group the controls under one Home Assistant device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Morning Briefing Settings",
        manufacturer="Parker's Morning Briefing",
    )


async def save_option(
    hass: HomeAssistant, entry: ConfigEntry, key: str, value: object
) -> None:
    """Persist a single option without touching credentials or other settings."""
    options = dict(entry.options)
    options[key] = value
    hass.config_entries.async_update_entry(entry, options=options)

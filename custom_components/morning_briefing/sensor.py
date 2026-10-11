"""Privacy-conscious last-run status entity."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from . import BriefingCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add the single run status sensor."""
    coordinator: BriefingCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MorningBriefingStatusSensor(coordinator, entry)])


class MorningBriefingStatusSensor(CoordinatorEntity[BriefingCoordinator], SensorEntity):
    """Expose status metadata only; never expose email/event facts."""

    _attr_has_entity_name = True
    _attr_name = "Last run"
    _attr_icon = "mdi:weather-sunset-up"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "last_run"

    def __init__(self, coordinator: BriefingCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_run"

    @property
    def native_value(self) -> str:
        """Return success, partial, or never-run."""
        return str(self.coordinator.data.get("status", "never_run"))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return timestamp and source status only."""
        return {
            "last_run": self.coordinator.data.get("last_run"),
            "sources": self.coordinator.data.get("sources", {}),
        }

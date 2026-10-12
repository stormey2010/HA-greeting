"""Config flow and options for the morning briefing."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.config_entries import OptionsFlowWithReload

from .const import (
    CONF_CEREBRAS_API_KEY,
    CONF_CEREBRAS_MODEL,
    CONF_CALDAV_PASSWORD,
    CONF_CALDAV_URL,
    CONF_CALDAV_USER,
    CONF_GMAIL_ENABLED,
    CONF_GMAIL_RECONNECT,
    DEFAULT_MODEL,
    DEFAULT_OPTIONS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MorningBriefingConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Set up the integration, optionally linking Gmail with HA-managed OAuth."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return the flow logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Ask Google for offline access to read selected Gmail message content."""
        return {
            "scope": "https://www.googleapis.com/auth/gmail.readonly",
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect the core API key and decide whether to link Gmail."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_CEREBRAS_API_KEY): selector.TextSelector(
                            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                        ),
                        vol.Optional(CONF_CEREBRAS_MODEL, default=DEFAULT_MODEL): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=["gpt-oss-120b", "qwen-3-32b", "llama3.1-8b"],
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                        vol.Optional(CONF_GMAIL_ENABLED, default=False): selector.BooleanSelector(),
                        vol.Optional(CONF_CALDAV_URL, default="https://caldav.icloud.com"): selector.TextSelector(),
                        vol.Optional(CONF_CALDAV_USER): selector.TextSelector(),
                        vol.Optional(CONF_CALDAV_PASSWORD): selector.TextSelector(
                            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                        ),
                    }
                ),
            )

        self.context["core_data"] = {
            CONF_CEREBRAS_API_KEY: user_input[CONF_CEREBRAS_API_KEY],
            CONF_CEREBRAS_MODEL: user_input.get(CONF_CEREBRAS_MODEL, DEFAULT_MODEL),
        }
        self.context["core_options"] = {
            **DEFAULT_OPTIONS,
            "caldav": {
                "url": user_input.get(CONF_CALDAV_URL, "https://caldav.icloud.com").strip(),
                "username": user_input.get(CONF_CALDAV_USER, "").strip(),
                "password": user_input.get(CONF_CALDAV_PASSWORD, ""),
            },
        }
        self.context["gmail_enabled"] = user_input.get(CONF_GMAIL_ENABLED, False)
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if self.context["gmail_enabled"]:
            return await self.async_step_pick_implementation()
        return self.async_create_entry(
            title="Morning Briefing",
            data=self.context["core_data"],
            options=self.context["core_options"],
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> config_entries.ConfigFlowResult:
        """Start Google's standard reauthentication flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Allow API-key correction and Gmail linking after initial setup."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            self.context["pending_data"] = {
                CONF_CEREBRAS_API_KEY: user_input.get(CONF_CEREBRAS_API_KEY, "").strip()
                or entry.data.get(CONF_CEREBRAS_API_KEY, ""),
                CONF_CEREBRAS_MODEL: user_input.get(CONF_CEREBRAS_MODEL, DEFAULT_MODEL),
            }
            self.context["pending_options"] = {
                **entry.options,
                CONF_GMAIL_ENABLED: user_input.get(CONF_GMAIL_ENABLED, False),
            }
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_mismatch()
            if user_input.get(CONF_GMAIL_ENABLED) and (
                entry.data.get("gmail_scope_version", 0) < 2 or user_input.get(CONF_GMAIL_RECONNECT)
            ):
                return await self.async_step_pick_implementation()
            return self.async_update_reload_and_abort(
                entry,
                data_updates=self.context["pending_data"],
                options=self.context["pending_options"],
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CEREBRAS_API_KEY, default=""): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(CONF_CEREBRAS_MODEL, default=entry.data.get(CONF_CEREBRAS_MODEL, DEFAULT_MODEL)): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["gpt-oss-120b", "qwen-3-32b", "llama3.1-8b"],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_GMAIL_ENABLED, default=entry.options.get(CONF_GMAIL_ENABLED, False)): selector.BooleanSelector(),
                    vol.Optional(CONF_GMAIL_RECONNECT, default=False): selector.BooleanSelector(),
                }
            ),
        )

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm the user wants to reconnect Google."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_pick_implementation()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> config_entries.ConfigFlowResult:
        """Create an entry or update its OAuth data without exposing tokens."""
        data = {**data, "gmail_scope_version": 2}
        if self.source == config_entries.SOURCE_REAUTH:
            entry = self._get_reauth_entry()
            return self.async_update_reload_and_abort(
                entry,
                data_updates=data,
                options={**entry.options, CONF_GMAIL_ENABLED: True},
            )
        if self.source == config_entries.SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            return self.async_update_reload_and_abort(
                entry,
                data_updates={**self.context.get("pending_data", {}), **data},
                options={**self.context.get("pending_options", entry.options), CONF_GMAIL_ENABLED: True},
            )
        return self.async_create_entry(
            title="Morning Briefing",
            data={**self.context.get("core_data", {}), **data},
            options={**self.context.get("core_options", DEFAULT_OPTIONS), CONF_GMAIL_ENABLED: True},
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "MorningBriefingOptionsFlow":
        """Return the options flow."""
        return MorningBriefingOptionsFlow()


class MorningBriefingOptionsFlow(OptionsFlowWithReload):
    """Manage calendar choices, sources and announcement settings."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show settings; selected CalDAV calendars can be added or removed here."""
        from .caldav import async_discover_calendars
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        current = {**DEFAULT_OPTIONS, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_GMAIL_ENABLED) and "token" not in self.config_entry.data:
                errors["base"] = "gmail_not_linked"
            else:
                caldav_settings = {
                    "url": user_input.pop(CONF_CALDAV_URL, caldav_value(self.config_entry, "url", "https://caldav.icloud.com")).strip(),
                    "username": user_input.pop(CONF_CALDAV_USER, caldav_value(self.config_entry, "username", "")).strip(),
                    "password": user_input.pop(CONF_CALDAV_PASSWORD, caldav_value(self.config_entry, "password", "")),
                }
                return self.async_create_entry(
                    title="", data={**user_input, "caldav": caldav_settings}
                )

        calendars: list[dict[str, str]] = []
        caldav = self.config_entry.options.get("caldav") or {}
        if caldav.get("url") and caldav.get("username") and caldav.get("password"):
            try:
                discovered = await async_discover_calendars(
                    async_get_clientsession(self.hass),
                    caldav["url"], caldav["username"], caldav["password"],
                )
                calendars = [{"label": c["name"], "value": c["name"]} for c in discovered]
            except Exception as err:  # Keep options editable when the calendar server is down.
                _LOGGER.debug("CalDAV calendar discovery failed (%s)", type(err).__name__)

        entity_opts = {
            "weather_entity": selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
            "calendar_entities": selector.EntitySelector(selector.EntitySelectorConfig(domain="calendar", multiple=True)),
            "todo_entities": selector.EntitySelector(selector.EntitySelectorConfig(domain="todo", multiple=True)),
            "presence_entities": selector.EntitySelector(selector.EntitySelectorConfig(domain="person", multiple=True)),
            "battery_entities": selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", multiple=True)),
            "speaker_script": selector.EntitySelector(selector.EntitySelectorConfig(domain="script")),
            "speaker_entity": selector.EntitySelector(selector.EntitySelectorConfig(domain="media_player")),
        }
        schema: dict[Any, Any] = {}
        for key in ("weather_enabled", "calendar_enabled", "todo_enabled", "presence_enabled", "batteries_enabled", CONF_GMAIL_ENABLED):
            schema[vol.Optional(key, default=current.get(key, False))] = selector.BooleanSelector()
        schema[vol.Optional("calendar_source", default=current["calendar_source"])] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=["caldav", "home_assistant"], mode=selector.SelectSelectorMode.DROPDOWN)
        )
        for key, field_selector in entity_opts.items():
            schema[vol.Optional(key, default=current.get(key, [] if key.endswith("entities") else ""))] = field_selector
        schema[vol.Optional("calendar_names", default=current.get("calendar_names", []))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=calendars, multiple=True, mode=selector.SelectSelectorMode.DROPDOWN)
        )
        schema[vol.Optional("calendar_labels", default=current.get("calendar_labels", ""))] = selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        )
        for key, default in ((CONF_CALDAV_URL, caldav.get("url", "https://caldav.icloud.com")),
                             (CONF_CALDAV_USER, caldav.get("username", ""))):
            schema[vol.Optional(key, default=default)] = selector.TextSelector()
        schema[vol.Optional(CONF_CALDAV_PASSWORD, default=caldav.get("password", ""))] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        for key, default, minimum, maximum in (
            ("low_battery_percent", 25, 1, 100),
            ("max_calendar_events", 8, 1, 30),
            ("max_todo_items", 4, 1, 20),
            ("max_gmail_messages", 4, 1, 5),
            ("speaker_volume", 29, 1, 100),
        ):
            schema[vol.Optional(key, default=current.get(key, default))] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=minimum, max=maximum, mode=selector.NumberSelectorMode.BOX, step=1)
            )
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema), errors=errors)


def caldav_value(entry: config_entries.ConfigEntry, key: str, default: str) -> str:
    """Read one saved CalDAV value without logging it."""
    return str((entry.options.get("caldav") or {}).get(key, default))

"""HASP-LVGL Commonalities."""
import logging

from homeassistant.core import callback
from homeassistant.helpers.entity import ToggleEntity
import voluptuous as vol

from .const import (
    CONF_PLATE,
    DOMAIN,
    EVENT_HASP_PLATE_OFFLINE,
    EVENT_HASP_PLATE_ONLINE,
    HASP_IDLE_STATES,
)

_LOGGER = logging.getLogger(__name__)


HASP_IDLE_SCHEMA = vol.Schema(vol.Any(*HASP_IDLE_STATES))


class HASPToggleEntity(ToggleEntity):
    """Representation of HASP ToggleEntity."""

    def __init__(self, hwid, topic):
        """Initialize the light."""
        super().__init__()
        self._topic = topic
        self._state = None
        self._hwid = hwid
        self._available = False
        self._subscriptions = []

    @property
    def available(self):
        """Return if entity is available."""
        return self._available

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    async def refresh(self):
        """Sync local state back to plate."""
        raise NotImplementedError()

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        @callback
        async def online(event):
            if event.data[CONF_PLATE] == self._hwid:
                self._available = True
                await self.refresh()

        self._subscriptions.append(
            self.hass.bus.async_listen(EVENT_HASP_PLATE_ONLINE, online)
        )

        @callback
        async def offline(event):
            if event.data[CONF_PLATE] == self._hwid:
                self._available = False
                self.async_write_ha_state()

        self._subscriptions.append(
            self.hass.bus.async_listen(EVENT_HASP_PLATE_OFFLINE, offline)
        )

    async def async_will_remove_from_hass(self):
        """Run when entity about to be removed."""
        await super().async_will_remove_from_hass()

        for subscription in self._subscriptions:
            subscription()

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._hwid)},
        }

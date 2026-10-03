"""Parser for Teltonika EYE sensor BLE advertisements.

Protocol: Teltonika wiki, "EYE SENSOR / BTSMP1", sensor advertising. Manufacturer specific
data (company 0x089A): protocol version 0x01, a flags byte, then the values that the flags
announce, big-endian, in this order: temperature, humidity, movement, angle, battery voltage.
"""

from __future__ import annotations

import logging
from struct import unpack

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import (
    BinarySensorDeviceClass,
    SensorDeviceClass,
    SensorLibrary,
    Units,
)

_LOGGER = logging.getLogger(__name__)

TELTONIKA_MANUFACTURER_ID = 0x089A
PROTOCOL_VERSION = 0x01

FLAG_TEMPERATURE = 1 << 0
FLAG_HUMIDITY = 1 << 1
FLAG_MAGNET_PRESENT = 1 << 2
FLAG_MAGNET_DETECTED = 1 << 3
FLAG_MOVEMENT = 1 << 4
FLAG_ANGLE = 1 << 5
FLAG_LOW_BATTERY = 1 << 6
FLAG_BATTERY_VOLTAGE = 1 << 7


class TeltonikaBluetoothDeviceData(BluetoothData):
    """Data for Teltonika EYE sensors (EYE SENSOR, EYE BEACON)."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        data = service_info.manufacturer_data.get(TELTONIKA_MANUFACTURER_ID)
        if data is None or len(data) < 2 or data[0] != PROTOCOL_VERSION:
            return
        flags, values = data[1], data[2:]
        if len(values) < _values_length(flags):
            _LOGGER.debug("Teltonika EYE advertisement too short: %s", data.hex())
            return
        _LOGGER.debug("Parsing Teltonika EYE advertisement: %s", data.hex())

        name = f"Teltonika EYE {short_address(service_info.address)}"
        self.set_device_type("EYE")
        self.set_device_manufacturer("Teltonika")
        self.set_device_name(name)
        self.set_title(name)

        if flags & FLAG_TEMPERATURE:
            (temperature,) = unpack(">h", values[0:2])
            self.update_predefined_sensor(SensorLibrary.TEMPERATURE__CELSIUS, temperature / 100)
            values = values[2:]
        if flags & FLAG_HUMIDITY:
            self.update_predefined_sensor(SensorLibrary.HUMIDITY__PERCENTAGE, values[0])
            values = values[1:]
        if flags & FLAG_MAGNET_PRESENT:
            self.update_binary_sensor(
                key="magnet",
                native_value=bool(flags & FLAG_MAGNET_DETECTED),
                device_class=BinarySensorDeviceClass.PRESENCE,
                name="Magnet",
            )
        if flags & FLAG_MOVEMENT:
            # Most significant bit: moving; the other 15 bits count movement events.
            (movement,) = unpack(">H", values[0:2])
            self.update_binary_sensor(
                key="moving",
                native_value=bool(movement & 0x8000),
                device_class=BinarySensorDeviceClass.MOVING,
                name="Moving",
            )
            self.update_sensor(
                key="moving_count",
                native_unit_of_measurement=None,
                native_value=movement & 0x7FFF,
                device_class=SensorDeviceClass.COUNT,
                name="Moving events",
            )
            values = values[2:]
        if flags & FLAG_ANGLE:
            (pitch, roll) = unpack(">bh", values[0:3])
            self.update_sensor(
                key="pitch", native_unit_of_measurement=Units.DEGREE, native_value=pitch, name="Pitch"
            )
            self.update_sensor(
                key="roll", native_unit_of_measurement=Units.DEGREE, native_value=roll, name="Roll"
            )
            values = values[3:]
        self.update_binary_sensor(
            key="low_battery",
            native_value=bool(flags & FLAG_LOW_BATTERY),
            device_class=BinarySensorDeviceClass.BATTERY,
            name="Low battery",
        )
        if flags & FLAG_BATTERY_VOLTAGE:
            self.update_predefined_sensor(
                SensorLibrary.VOLTAGE__ELECTRIC_POTENTIAL_VOLT, (2000 + values[0] * 10) / 1000
            )


def _values_length(flags: int) -> int:
    """Return how many value bytes the flags announce."""
    return (
        (2 if flags & FLAG_TEMPERATURE else 0)
        + (1 if flags & FLAG_HUMIDITY else 0)
        + (2 if flags & FLAG_MOVEMENT else 0)
        + (3 if flags & FLAG_ANGLE else 0)
        + (1 if flags & FLAG_BATTERY_VOLTAGE else 0)
    )

"""Parser for Eddystone-TLM BLE advertisements.

Spec: https://github.com/google/eddystone/blob/master/eddystone-tlm/tlm-plain.md
"""

from __future__ import annotations

import logging
from struct import unpack

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import SensorLibrary

_LOGGER = logging.getLogger(__name__)

EDDYSTONE_SERVICE_UUID = "0000feaa-0000-1000-8000-00805f9b34fb"

TLM_FRAME_TYPE = 0x20
TLM_VERSION_UNENCRYPTED = 0x00
TLM_LENGTH = 14

# Values a beacon sends when it cannot measure them.
VOLTAGE_NOT_SUPPORTED = 0
TEMPERATURE_NOT_SUPPORTED = -0x8000


class EddystoneBluetoothDeviceData(BluetoothData):
    """Data for Eddystone-TLM beacons.

    The same service UUID also carries Eddystone UID/URL/EID frames, which are
    ignored. TLM temperature is the beacon's chip temperature, not that of a
    separate sensor.
    """

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        data = service_info.service_data.get(EDDYSTONE_SERVICE_UUID)
        if (
            data is None
            or len(data) != TLM_LENGTH
            or data[0] != TLM_FRAME_TYPE
            or data[1] != TLM_VERSION_UNENCRYPTED
        ):
            return
        _LOGGER.debug("Parsing Eddystone-TLM advertisement: %s", data.hex())

        name = f"Eddystone TLM {short_address(service_info.address)}"
        self.set_device_type("Eddystone TLM")
        self.set_device_manufacturer("Eddystone")
        self.set_device_name(name)
        self.set_title(name)

        # Battery voltage in mV, temperature in signed 8.8 fixed-point °C.
        (voltage, temperature) = unpack(">Hh", data[2:6])
        if voltage != VOLTAGE_NOT_SUPPORTED:
            self.update_predefined_sensor(
                SensorLibrary.VOLTAGE__ELECTRIC_POTENTIAL_VOLT, voltage / 1000
            )
        if temperature != TEMPERATURE_NOT_SUPPORTED:
            self.update_predefined_sensor(
                SensorLibrary.TEMPERATURE__CELSIUS, round(temperature / 256, 2)
            )

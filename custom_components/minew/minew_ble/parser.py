"""Parser for Minew BLE advertisements.

Frame layout as decoded by reelyActive's advlib-ble-services (MIT):
https://github.com/reelyactive/advlib-ble-services/blob/master/lib/minew.js
"""

from __future__ import annotations

import logging
from struct import unpack

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import SensorLibrary

_LOGGER = logging.getLogger(__name__)

MINEW_SERVICE_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

MINEW_FRAME_TYPE = 0xA1
# 0x13 is the documented temperature frame. E9 beacons with Minew's proprietary firmware
# send the same layout with version 0x99.
TEMPERATURE_VERSIONS = (0x13, 0x99)
TEMPERATURE_LENGTH = 11


class MinewBluetoothDeviceData(BluetoothData):
    """Data for Minew sensor beacons.

    Minew sends several frames under frame type 0xA1 (info, acceleration, ...),
    told apart by the version byte after it. Only the temperature frame, as sent
    by the E9, is supported.
    """

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        data = service_info.service_data.get(MINEW_SERVICE_UUID)
        if (
            data is None
            or len(data) != TEMPERATURE_LENGTH
            or data[0] != MINEW_FRAME_TYPE
            or data[1] not in TEMPERATURE_VERSIONS
        ):
            return
        _LOGGER.debug("Parsing Minew temperature advertisement: %s", data.hex())

        name = f"Minew {short_address(service_info.address)}"
        self.set_device_type("Temperature beacon")
        self.set_device_manufacturer("Minew")
        self.set_device_name(name)
        self.set_title(name)

        # Battery in %, temperature in signed 8.8 fixed-point °C.
        (battery, temperature) = unpack(">Bh", data[2:5])
        self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, battery)
        self.update_predefined_sensor(
            SensorLibrary.TEMPERATURE__CELSIUS, round(temperature / 256, 2)
        )

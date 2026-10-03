"""Parser for ELA Innovation BLE tags (Blue PUCK, Blue COIN).

Spec: ELA Innovation "BLE Frame specifications" 11B. Tags send their sensor data either
as Bluetooth service data (default) or as manufacturer specific data (company 0x0757,
"Mfr. Data Enable" in the NFC configuration, firmware >= 2.0.0).
"""

from __future__ import annotations

from enum import StrEnum
import logging
from struct import unpack

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import BinarySensorDeviceClass, SensorDeviceClass, SensorLibrary

_LOGGER = logging.getLogger(__name__)

ELA_MANUFACTURER_ID = 0x0757


def _uuid16(uuid: int) -> str:
    return f"0000{uuid:04x}-0000-1000-8000-00805f9b34fb"


TEMPERATURE_UUID = _uuid16(0x2A6E)
HUMIDITY_UUID = _uuid16(0x2A6F)
ALERT_LEVEL_UUID = _uuid16(0x2A06)
ALERT_STATUS_UUID = _uuid16(0x2A3F)
BATTERY_SERVICE_UUID = _uuid16(0x180F)  # battery % before firmware 2.2.0
BATTERY_LEVEL_UUID = _uuid16(0x2A19)  # battery % from firmware 2.2.0

# Manufacturer specific data: first byte after the company ID.
MFR_TEMPERATURE = 0x12
MFR_HUMIDITY_TEMPERATURE = 0x21
MFR_MAGNET = 0x32
MFR_MOVEMENT = 0x42
MFR_DIGITAL_INPUT = 0x62
MFR_BATTERY_PERCENTAGE = 0xF1
MFR_BATTERY_VOLTAGE = 0xF2


class ElaFormat(StrEnum):
    """Tag formats (the sensor a tag reports)."""

    TEMPERATURE = "T"
    HUMIDITY_TEMPERATURE = "RHT"
    MAGNET = "MAG"
    MOVEMENT = "MOV"
    DIGITAL_INPUT = "DI"


# Alert status (0x2A3F) value telling MAG, MOV and DI apart in service data mode.
ALERT_STATUS_FORMATS = {
    0x00: ElaFormat.MAGNET,
    0x01: ElaFormat.MOVEMENT,
    0x02: ElaFormat.DIGITAL_INPUT,
}
MFR_EVENT_FORMATS = {
    MFR_MAGNET: ElaFormat.MAGNET,
    MFR_MOVEMENT: ElaFormat.MOVEMENT,
    MFR_DIGITAL_INPUT: ElaFormat.DIGITAL_INPUT,
}
# Firmware 1.0.0 sends no alert status; the default tag name ("P MAG 123456",
# "C MOV 123456") still tells the format.
NAME_FORMATS = {"MAG": ElaFormat.MAGNET, "MOV": ElaFormat.MOVEMENT}

EVENT_SENSORS: dict[ElaFormat, tuple[str, BinarySensorDeviceClass, str]] = {
    ElaFormat.MAGNET: ("magnet", BinarySensorDeviceClass.PRESENCE, "Magnet"),
    ElaFormat.MOVEMENT: ("moving", BinarySensorDeviceClass.MOVING, "Moving"),
    ElaFormat.DIGITAL_INPUT: ("input", BinarySensorDeviceClass.GENERIC, "Input"),
}


class ElaBluetoothDeviceData(BluetoothData):
    """Data for ELA Innovation tags.

    MAG, MOV and DI tags send a 16-bit value: bit 0 is the state (magnet present,
    moving, input active) and the other 15 bits count the state changes.
    Battery information only comes in the scan response, and only below 15 % unless
    the tag is configured to send its voltage (firmware >= 3.0.0).
    """

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        if (mfr_data := service_info.manufacturer_data.get(ELA_MANUFACTURER_ID)) is not None:
            self._parse_manufacturer_data(service_info, mfr_data)
        self._parse_service_data(service_info)

    def _parse_service_data(self, service_info: BluetoothServiceInfo) -> None:
        service_data = service_info.service_data
        if (temperature := service_data.get(TEMPERATURE_UUID)) is not None and len(temperature) == 2:
            humidity = service_data.get(HUMIDITY_UUID)
            if humidity is not None and len(humidity) == 1:
                self._set_device(service_info, ElaFormat.HUMIDITY_TEMPERATURE)
                self.update_predefined_sensor(SensorLibrary.HUMIDITY__PERCENTAGE, humidity[0])
            else:
                self._set_device(service_info, ElaFormat.TEMPERATURE)
            self._update_temperature(temperature)

        if (alert_level := service_data.get(ALERT_LEVEL_UUID)) is not None and len(alert_level) == 2:
            alert_status = service_data.get(ALERT_STATUS_UUID)
            if alert_status is not None and len(alert_status) == 1:
                tag_format = ALERT_STATUS_FORMATS.get(alert_status[0])
            else:
                tag_format = NAME_FORMATS.get(service_info.name[2:5])
            if tag_format is not None:
                self._set_device(service_info, tag_format)
                self._update_event(tag_format, alert_level)

        for uuid in (BATTERY_LEVEL_UUID, BATTERY_SERVICE_UUID):
            if (battery := service_data.get(uuid)) is not None and len(battery) >= 1:
                self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, battery[0])

    def _parse_manufacturer_data(self, service_info: BluetoothServiceInfo, data: bytes) -> None:
        if not data:
            return
        frame_id, payload = data[0], data[1:]
        if frame_id == MFR_TEMPERATURE and len(payload) >= 2:
            self._set_device(service_info, ElaFormat.TEMPERATURE)
            self._update_temperature(payload[0:2])
        elif (
            frame_id == MFR_HUMIDITY_TEMPERATURE
            and len(payload) >= 4
            and payload[1] == MFR_TEMPERATURE
        ):
            self._set_device(service_info, ElaFormat.HUMIDITY_TEMPERATURE)
            self.update_predefined_sensor(SensorLibrary.HUMIDITY__PERCENTAGE, payload[0])
            self._update_temperature(payload[2:4])
        elif (tag_format := MFR_EVENT_FORMATS.get(frame_id)) is not None and len(payload) >= 2:
            self._set_device(service_info, tag_format)
            self._update_event(tag_format, payload[0:2])
        elif frame_id == MFR_BATTERY_PERCENTAGE and len(payload) >= 1:
            self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, payload[0])
        elif frame_id == MFR_BATTERY_VOLTAGE and len(payload) >= 2:
            (voltage,) = unpack("<H", payload[0:2])
            self.update_predefined_sensor(
                SensorLibrary.VOLTAGE__ELECTRIC_POTENTIAL_VOLT, voltage / 1000
            )

    def _set_device(self, service_info: BluetoothServiceInfo, tag_format: ElaFormat) -> None:
        _LOGGER.debug("Parsing ELA %s advertisement from %s", tag_format, service_info.address)
        name = f"ELA {tag_format} {short_address(service_info.address)}"
        self.set_device_type(tag_format.value)
        self.set_device_manufacturer("ELA Innovation")
        self.set_device_name(name)
        self.set_title(name)

    def _update_temperature(self, data: bytes) -> None:
        (temperature,) = unpack("<h", data)
        self.update_predefined_sensor(SensorLibrary.TEMPERATURE__CELSIUS, temperature / 100)

    def _update_event(self, tag_format: ElaFormat, data: bytes) -> None:
        (value,) = unpack("<H", data)
        key, device_class, name = EVENT_SENSORS[tag_format]
        self.update_binary_sensor(
            key=key, native_value=bool(value & 1), device_class=device_class, name=name
        )
        self.update_sensor(
            key=f"{key}_count",
            native_unit_of_measurement=None,
            native_value=value >> 1,
            device_class=SensorDeviceClass.COUNT,
            name=f"{name} events",
        )

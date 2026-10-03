"""Tests for the ELA Innovation parser.

Frames are the examples from ELA's "BLE Frame specifications" 11B, unless noted as captured.
"""

from ela_ble import ElaBluetoothDeviceData
from ela_ble.parser import (
    ALERT_LEVEL_UUID,
    ALERT_STATUS_UUID,
    BATTERY_SERVICE_UUID,
    ELA_MANUFACTURER_ID,
    HUMIDITY_UUID,
    TEMPERATURE_UUID,
)

from helpers import advertisement, binary_values, values


def parse(**kwargs: object) -> object:
    return ElaBluetoothDeviceData().update(advertisement(**kwargs))


def test_temperature_service_data() -> None:
    update = parse(service_data={TEMPERATURE_UUID: "6c0a"}, name="P T 801803")
    assert update.title == "ELA T EEFF"
    assert values(update) == {"temperature": 26.68, "signal_strength": -60}


def test_temperature_manufacturer_data() -> None:
    update = parse(manufacturer_data={ELA_MANUFACTURER_ID: "12850a"})
    assert values(update) == {"temperature": 26.93, "signal_strength": -60}


def test_negative_temperature() -> None:
    update = parse(service_data={TEMPERATURE_UUID: "38ff"})
    assert values(update)["temperature"] == -2.0


def test_captured_temperature_tag_with_battery() -> None:
    # Captured from BT01078: 21.18 °C, battery 15 % in the pre-2.2.0 battery service.
    update = parse(service_data={TEMPERATURE_UUID: "4608", BATTERY_SERVICE_UUID: "0f"})
    assert values(update) == {"temperature": 21.18, "battery": 15, "signal_strength": -60}


def test_humidity_temperature() -> None:
    service = parse(service_data={TEMPERATURE_UUID: "8a0a", HUMIDITY_UUID: "2f"})
    assert service.title == "ELA RHT EEFF"
    assert values(service) == {"temperature": 26.98, "humidity": 47, "signal_strength": -60}
    mfr = parse(manufacturer_data={ELA_MANUFACTURER_ID: "213012b80a"})
    assert values(mfr) == {"temperature": 27.44, "humidity": 48, "signal_strength": -60}


def test_magnet() -> None:
    service = parse(service_data={ALERT_LEVEL_UUID: "0900", ALERT_STATUS_UUID: "00"})
    assert service.title == "ELA MAG EEFF"
    assert binary_values(service) == {"magnet": True}
    assert values(service)["magnet_count"] == 4
    mfr = parse(manufacturer_data={ELA_MANUFACTURER_ID: "320a00"})
    assert binary_values(mfr) == {"magnet": False}
    assert values(mfr)["magnet_count"] == 5


def test_magnet_firmware_1_by_name() -> None:
    update = parse(service_data={ALERT_LEVEL_UUID: "0900"}, name="P MAG C0062E")
    assert binary_values(update) == {"magnet": True}


def test_movement() -> None:
    service = parse(service_data={ALERT_LEVEL_UUID: "0700", ALERT_STATUS_UUID: "01"})
    assert service.title == "ELA MOV EEFF"
    assert binary_values(service) == {"moving": True}
    assert values(service)["moving_count"] == 3
    mfr = parse(manufacturer_data={ELA_MANUFACTURER_ID: "420c00"})
    assert binary_values(mfr) == {"moving": False}
    assert values(mfr)["moving_count"] == 6


def test_digital_input() -> None:
    service = parse(service_data={ALERT_LEVEL_UUID: "0a00", ALERT_STATUS_UUID: "02"})
    assert service.title == "ELA DI EEFF"
    assert binary_values(service) == {"input": False}
    assert values(service)["input_count"] == 5
    mfr = parse(manufacturer_data={ELA_MANUFACTURER_ID: "620a00"})
    assert binary_values(mfr) == {"input": False}


def test_captured_digital_input() -> None:
    # Captured from BT01001: 0x0031 is odd, so the input is on; 49 >> 1 = 24 events.
    update = parse(service_data={ALERT_LEVEL_UUID: "3100", ALERT_STATUS_UUID: "02"})
    assert binary_values(update) == {"input": True}
    assert values(update)["input_count"] == 24


def test_battery_scan_response() -> None:
    percentage = parse(manufacturer_data={ELA_MANUFACTURER_ID: "f10d"})
    assert values(percentage)["battery"] == 13
    voltage = parse(manufacturer_data={ELA_MANUFACTURER_ID: "f2ac0b"})
    assert values(voltage)["voltage"] == 2.988


def test_unknown_alert_tag_is_ignored() -> None:
    # Alert level without alert status or a recognisable name: format unknown.
    assert not ElaBluetoothDeviceData().supported(
        advertisement(service_data={ALERT_LEVEL_UUID: "0900"}, name="BT01001")
    )

"""Tests for the Teltonika EYE parser."""

from teltonika_ble import TeltonikaBluetoothDeviceData
from teltonika_ble.parser import TELTONIKA_MANUFACTURER_ID

from helpers import advertisement, binary_values, values


def parse(payload: str) -> object:
    return TeltonikaBluetoothDeviceData().update(
        advertisement(manufacturer_data={TELTONIKA_MANUFACTURER_ID: payload})
    )


def test_all_values() -> None:
    # Example from the Teltonika wiki: flags 0xB7, 22.28 °C, 18 %, magnet present but no
    # field, not moving with 3275 events, pitch 11°, roll -57°, 3030 mV.
    update = parse("01b708b4120ccb0bffc767")
    assert update.title == "Teltonika EYE EEFF"
    assert values(update) == {
        "temperature": 22.28,
        "humidity": 18,
        "moving_count": 3275,
        "pitch": 11,
        "roll": -57,
        "voltage": 3.03,
        "signal_strength": -60,
    }
    assert binary_values(update) == {"magnet": False, "moving": False, "low_battery": False}


def test_magnet_detected_and_low_battery() -> None:
    update = parse("014c")
    assert binary_values(update) == {"magnet": True, "low_battery": True}


def test_moving_and_negative_temperature() -> None:
    update = parse("0111ff388005")
    assert values(update)["temperature"] == -2.0
    assert binary_values(update)["moving"] is True
    assert values(update)["moving_count"] == 5


def test_invalid_frames_are_ignored() -> None:
    for payload in ("02b708b4120ccb0bffc767", "01b708b4", "01"):
        assert not TeltonikaBluetoothDeviceData().supported(
            advertisement(manufacturer_data={TELTONIKA_MANUFACTURER_ID: payload})
        )

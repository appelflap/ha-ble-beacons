"""Tests for the Minew parser. Frames are taken from the advlib-ble-services unit tests."""

from minew_ble import MinewBluetoothDeviceData
from minew_ble.parser import MINEW_SERVICE_UUID

from helpers import service_info, values


def test_temperature_frame() -> None:
    device = MinewBluetoothDeviceData()
    assert device.supported(service_info(MINEW_SERVICE_UUID, "a113631973aabbccddeeff"))
    update = device.update(service_info(MINEW_SERVICE_UUID, "a113631973aabbccddeeff"))
    assert update.title == "Minew EEFF"
    assert values(update) == {"temperature": 25.45, "battery": 99, "signal_strength": -60}


def test_negative_temperature() -> None:
    update = MinewBluetoothDeviceData().update(
        service_info(MINEW_SERVICE_UUID, "a11363fb80aabbccddeeff")
    )
    assert values(update)["temperature"] == -4.5


def test_other_minew_frames_are_ignored() -> None:
    # TVOC frame: same length as the temperature frame, different version byte.
    assert not MinewBluetoothDeviceData().supported(
        service_info(MINEW_SERVICE_UUID, "a112634000aabbccddeeff")
    )


def test_proprietary_temperature_frame() -> None:
    # Captured from an E9 (AC:23:3F:AB:F3:05) that sends version 0x99 instead of 0x13.
    update = MinewBluetoothDeviceData().update(
        service_info(MINEW_SERVICE_UUID, "a19964171105f3ab3f23ac")
    )
    assert values(update) == {"temperature": 23.07, "battery": 100, "signal_strength": -60}

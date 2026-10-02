"""Tests for the Eddystone-TLM parser."""

from eddystone_ble import EddystoneBluetoothDeviceData
from eddystone_ble.parser import EDDYSTONE_SERVICE_UUID

from helpers import service_info, values

# Example frame from custom-components/ble_monitor#1562: 3183 mV, 30.0 °C.
TLM = "20000c6f1e000002006d41db9ab6"


def test_tlm() -> None:
    device = EddystoneBluetoothDeviceData()
    assert device.supported(service_info(EDDYSTONE_SERVICE_UUID, TLM))
    update = device.update(service_info(EDDYSTONE_SERVICE_UUID, TLM))
    assert update.title == "Eddystone TLM EEFF"
    assert values(update) == {"temperature": 30.0, "voltage": 3.183, "signal_strength": -60}


def test_tlm_negative_temperature() -> None:
    device = EddystoneBluetoothDeviceData()
    update = device.update(service_info(EDDYSTONE_SERVICE_UUID, "20000c6ffb800002006d41db9ab6"))
    assert values(update)["temperature"] == -4.5


def test_tlm_unsupported_readings_are_left_out() -> None:
    device = EddystoneBluetoothDeviceData()
    update = device.update(service_info(EDDYSTONE_SERVICE_UUID, "2000000080000002006d41db9ab6"))
    assert values(update) == {"signal_strength": -60}


def test_other_eddystone_frames_are_ignored() -> None:
    uid_frame = "00e8" + "00" * 16 + "0000"
    encrypted_tlm = "2001" + "00" * 12
    for payload in (uid_frame, encrypted_tlm):
        assert not EddystoneBluetoothDeviceData().supported(
            service_info(EDDYSTONE_SERVICE_UUID, payload)
        )

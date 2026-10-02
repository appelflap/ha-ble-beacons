"""Test helpers."""

from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceKey, SensorUpdate

ADDRESS = "AA:BB:CC:DD:EE:FF"


def service_info(uuid: str, payload: str) -> BluetoothServiceInfo:
    """Build a non-connectable advertisement carrying one service data entry."""
    return BluetoothServiceInfo(
        name="",
        address=ADDRESS,
        rssi=-60,
        manufacturer_data={},
        service_data={uuid: bytes.fromhex(payload)},
        service_uuids=[uuid],
        source="local",
    )


def values(update: SensorUpdate) -> dict[str, float | int | None]:
    """Map sensor keys to their values."""
    return {
        key.key: value.native_value
        for key, value in update.entity_values.items()
        if isinstance(key, DeviceKey)
    }

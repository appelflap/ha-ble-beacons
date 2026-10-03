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


def advertisement(
    service_data: dict[str, str] | None = None,
    manufacturer_data: dict[int, str] | None = None,
    name: str = "",
) -> BluetoothServiceInfo:
    """Build a non-connectable advertisement from hex payloads."""
    service_data = {uuid: bytes.fromhex(data) for uuid, data in (service_data or {}).items()}
    return BluetoothServiceInfo(
        name=name,
        address=ADDRESS,
        rssi=-60,
        manufacturer_data={
            company: bytes.fromhex(data) for company, data in (manufacturer_data or {}).items()
        },
        service_data=service_data,
        service_uuids=list(service_data),
        source="local",
    )


def binary_values(update: SensorUpdate) -> dict[str, bool | None]:
    """Map binary sensor keys to their values."""
    return {key.key: value.native_value for key, value in update.binary_entity_values.items()}


def values(update: SensorUpdate) -> dict[str, float | int | None]:
    """Map sensor keys to their values."""
    return {
        key.key: value.native_value
        for key, value in update.entity_values.items()
        if isinstance(key, DeviceKey)
    }

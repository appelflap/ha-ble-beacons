"""Parser for Teltonika BLE advertisements."""

from __future__ import annotations

from sensor_state_data import (
    BinarySensorDeviceClass,
    BinarySensorValue,
    DeviceKey,
    SensorDescription,
    SensorDeviceClass,
    SensorDeviceInfo,
    SensorUpdate,
    SensorValue,
    Units,
)

from .parser import TeltonikaBluetoothDeviceData

__all__ = [
    "TeltonikaBluetoothDeviceData",
    "BinarySensorDeviceClass",
    "BinarySensorValue",
    "DeviceKey",
    "SensorDescription",
    "SensorDeviceClass",
    "SensorDeviceInfo",
    "SensorUpdate",
    "SensorValue",
    "Units",
]

# Home Assistant BLE beacon integrations

Core-style Home Assistant integrations for BLE beacons, built on Home Assistant's own
Bluetooth integration (local adapters and ESPHome Bluetooth proxies). They follow the pattern
of core integrations such as `kegtron` and `thermobeacon`, so they can become core
integrations later.

| Integration | Frame | Sensors |
|---|---|---|
| `eddystone` | Eddystone-TLM, unencrypted (service UUID `0xFEAA`, frame `0x20`), [spec](https://github.com/google/eddystone/blob/master/eddystone-tlm/tlm-plain.md) | temperature (chip temperature), battery voltage, signal strength |
| `ela` | ELA Innovation Blue PUCK/COIN tags (service data, or manufacturer data `0x0757`): T, RHT, MAG, MOV, DI, per ELA's "BLE Frame specifications" 11B | temperature, humidity, magnet/moving/input (on/off) with event counters, battery %, battery voltage, signal strength |
| `minew` | Minew temperature frame (service UUID `0xFFE1`, frame `0xA1`, version `0x13`, or `0x99` on some E9 firmware), layout per [advlib-ble-services](https://github.com/reelyactive/advlib-ble-services/blob/master/lib/minew.js) | temperature, battery %, signal strength |

Devices are only offered for setup at -50 dBm or stronger (`MIN_DISCOVERY_RSSI`), so the
beacons of the neighbours are not. Hold a beacon close to an adapter or proxy to add it.

## Brand icons

- `eddystone`: the Eddystone mark from [google/eddystone](https://github.com/google/eddystone/tree/master/branding)
  (`EddyStone_final-02.svg`), drawn black for light and white for dark themes.
- `ela`: the node mark from ELA Innovation's logo (GitHub avatar of [elaInnovation](https://github.com/elaInnovation)),
  traced to a vector shape.
- `minew`: the mark from Minew's logo (GitHub avatar of [MinewTech](https://github.com/MinewTech)), traced to
  a vector shape so it stays sharp at 256 and 512 px.

## Layout

Each integration vendors its parser in a sub-package (`ela_ble`, `eddystone_ble`, `minew_ble`) that only
depends on `bluetooth-sensor-state-data`, `sensor-state-data` and `bluetooth-data-tools`
(all shipped with Home Assistant). These are meant to become PyPI libraries.

## Tests

The parser tests run without Home Assistant:

```
docker run --rm -v "$PWD":/src:ro python:3.14-slim sh -c 'pip install -q pytest \
  bluetooth-sensor-state-data sensor-state-data bluetooth-data-tools home-assistant-bluetooth \
  && cp -r /src /w && cd /w && python -m pytest -q tests'
```

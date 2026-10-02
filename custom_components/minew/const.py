"""Constants for the Minew integration."""

DOMAIN = "minew"

# Only devices at least this strong (dBm) are offered for setup, so the beacons of the
# neighbours are not. Hold a beacon close to an adapter or proxy to add it.
MIN_DISCOVERY_RSSI = -50

# Source Code Directory

This directory contains the main application source code.

## Structure

```
src/
├── http-server/        # Flask HTTP API server
└── wifi-manager/       # WiFi hotspot management
```

## HTTP Server (`http-server/`)
Flask-based HTTP API server that provides:
- Device information endpoints (`/device/info`, `/health`)
- Configuration management (`/api/set-seed-phrase`, `/api/set-provider-id`, etc.)
- WiFi setup endpoint (`/setup/wifi`)
- Mining provider control (`/api/provider/start|stop|status|restart`)

**Main file:** `server.py`

## WiFi Manager (`wifi-manager/`)
Python module for WiFi hotspot management:
- Creates WiFi access point with hostapd + dnsmasq
- Manages device ID generation
- Handles DHCP client tracking
- Provides hotspot status monitoring

**Main file:** `wifi_manager.py`

## Dependencies

All Python dependencies are listed in `/requirements.txt` at the repository root.

## Usage

These modules are used by:
- Main service: `/opt/rng-miner/start.sh` → starts HTTP server
- WiFi setup: Called by start.sh when no WiFi connection exists
- WiFi connection: Called by HTTP server when user configures WiFi

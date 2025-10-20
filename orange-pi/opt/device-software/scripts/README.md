# Scripts Directory

This directory contains all auxiliary scripts organized by purpose.

## Directory Structure

```
scripts/
├── core/           # Core functionality scripts
├── setup/          # Setup and configuration scripts
├── utils/          # Utility and diagnostic scripts
└── tests/          # Test scripts
```

## Core Scripts (`core/`)
Essential scripts for core device functionality:
- **wifi_connect.py** - Handles WiFi client connection with AP fallback
- **start_ap_direct.sh** - Emergency WiFi hotspot fallback (direct method)

## Setup Scripts (`setup/`)
One-time setup and configuration:
- **generate-config.sh** - Generates device ID and initial configuration

## Utility Scripts (`utils/`)
Diagnostic and maintenance tools:
- **diagnostics.sh** - Comprehensive system diagnostics (was test.sh)
- **fix_resolvconf.sh** - Fixes DNS resolution conflicts (was kill-resolvconf.sh)
- **force-restart.sh** - Forces clean restart of all services
- **wifi_status.sh** - Checks WiFi status

## Test Scripts (`tests/`)
Testing and verification:
- **test_server.sh** - Tests HTTP server endpoints
- **run-tests.sh** - Runs test suite

## Usage

All scripts are called by the main entry points:
- `/opt/rng-miner/start.sh` - Main startup (uses core/ scripts)
- `/opt/rng-miner/stop.sh` - Clean shutdown
- `/opt/rng-miner/install.sh` - Installation (uses setup/ scripts)

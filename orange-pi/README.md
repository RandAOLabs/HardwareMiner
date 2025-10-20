# RNG Miner Orange Pi Setup

Simple, one-step deployment for Orange Pi devices.

## Quick Install

1. **Flash Armbian** to your Orange Pi Zero 3
2. **Copy this entire folder** to the Orange Pi
3. **Run the installer**:
   ```bash
   sudo ./install.sh
   ```
4. **Reboot** the device:
   ```bash
   sudo reboot
   ```

## What Gets Installed

- ✅ **HTTP server** on port 8080 (HTTPS with self-signed cert)
- ✅ **WiFi hotspot** with SSID: `RNG-Miner-XXXXXXXX`
- ✅ **Device configuration** and management
- ✅ **Auto-start** services on boot
- ✅ **Docker** for future mining software

## After Installation

1. **Disconnect ethernet/WiFi** before rebooting
2. **Look for WiFi hotspot**: `RNG-Miner-XXXXXXXX`
3. **Connect with password**: `RNG-Miner-Password-123`
4. **Use mobile app** to configure the device

## Device URLs

- **Web interface**: `https://192.168.12.1:8080`
- **Health check**: `https://192.168.12.1:8080/health`
- **Device info**: `https://192.168.12.1:8080/device/info`

## Service Management

```bash
# Check status
sudo systemctl status rng-miner

# Start/stop/restart
sudo systemctl start rng-miner
sudo systemctl stop rng-miner
sudo systemctl restart rng-miner

# View logs
sudo journalctl -u rng-miner -f

# Manual control
sudo /opt/rng-miner/start.sh
sudo /opt/rng-miner/stop.sh
sudo /opt/rng-miner/restart.sh
```

## Repository Structure

```
orange-pi/
├── README.md                   # This file
├── API_DOCUMENTATION.md        # API endpoint documentation
├── requirements.txt            # Python dependencies
│
├── install.sh                  # One-time installation script
├── start.sh                    # Main service startup (used by systemd)
├── stop.sh                     # Service shutdown
├── restart.sh                  # Service restart
│
└── opt/device-software/
    ├── src/
    │   ├── http-server/
    │   │   └── server.py             # Flask HTTP API server
    │   └── wifi-manager/
    │       └── wifi_manager.py       # WiFi hotspot management
    │
    ├── scripts/
    │   ├── core/                     # Core functionality
    │   │   ├── wifi_connect.py       # WiFi client connection
    │   │   └── start_ap_direct.sh    # Emergency AP fallback
    │   ├── setup/                    # Setup scripts
    │   │   └── generate-config.sh    # Device ID generation
    │   ├── utils/                    # Utilities and diagnostics
    │   │   ├── diagnostics.sh        # System diagnostics
    │   │   ├── fix_resolvconf.sh     # DNS fix utility
    │   │   ├── force-restart.sh      # Force clean restart
    │   │   └── wifi_status.sh        # WiFi status checker
    │   └── tests/                    # Test scripts
    │       ├── test_server.sh        # HTTP server tests
    │       └── run-tests.sh          # Test runner
    │
    └── tests/
        ├── test_http_server.py       # HTTP server unit tests
        ├── test_wifi_hotspot.py      # WiFi hotspot tests
        └── requirements-test.txt     # Test dependencies
```

## Troubleshooting

**Hotspot not appearing:**
```bash
sudo systemctl restart rng-miner
sudo journalctl -u rng-miner -f
```

**Run diagnostics:**
```bash
sudo /opt/device-software/scripts/utils/diagnostics.sh
```

**Check WiFi status:**
```bash
sudo /opt/device-software/scripts/utils/wifi_status.sh
```

**Manual hotspot start:**
```bash
sudo python3 /opt/device-software/src/wifi-manager/wifi_manager.py start_hotspot
```

## Expected Device ID Format

Device ID will be 8 characters like: `A1B2C3D4`
Generated from hardware MAC address and machine ID.
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

## Files Included

- `install.sh` - Main installation script
- `server.py` - HTTP server with all endpoints
- `wifi_manager.py` - WiFi hotspot and connection management
- `requirements.txt` - Python dependencies
- `generate-config.sh` - SSL certificate generation
- `start.sh`, `stop.sh`, `restart.sh` - Service control scripts

## Troubleshooting

**Hotspot not appearing:**
```bash
sudo systemctl restart rng-miner
sudo journalctl -u rng-miner -f
```

**Check WiFi status:**
```bash
sudo /opt/rng-miner/venv/bin/python3 -c "
from wifi_manager import WiFiManager
print(WiFiManager().get_hotspot_status())
"
```

**Manual hotspot start:**
```bash
cd /opt/rng-miner
sudo ./venv/bin/python3 -c "
from wifi_manager import WiFiManager
WiFiManager().start_hotspot()
"
```

## Expected Device ID Format

Device ID will be 8 characters like: `A1B2C3D4`
Generated from hardware MAC address and machine ID.
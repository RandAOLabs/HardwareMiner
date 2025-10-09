# WiFi Connection Fix - Deployment Guide

## What Was Fixed

The WiFi credential handling was broken because the `/setup/wifi` endpoint was only saving credentials but never actually attempting to connect. The teardown and reconnection logic existed but was never called.

### Key Changes from Failed Attempts:

**Critical fixes based on testing:**
1. **Interface must be UP before NetworkManager restart** - We were bringing interface up AFTER NM restart, causing it to not be detected
2. **NetworkManager needs stabilization time** - Added 5+ second waits and status checks before attempting scan/connect
3. **systemd-resolved must be started** - Old approach starts it back up, we were leaving it stopped
4. **wpa_supplicant restart required** - Must restart wpa_supplicant before connection attempts
5. **Graceful shutdown first** - Stop services gracefully before killing processes
6. **Wait for NM to recognize wlan0** - Poll `nmcli device status` until wlan0 is not "unavailable/unmanaged"

## Changes Made

### 1. Server Endpoint (`/opt/device-software/src/http-server/server.py`)
- Modified `/setup/wifi` endpoint to trigger background WiFi connection
- Launches `wifi_connect.py` script in a background thread
- Returns immediately so the API doesn't hang

### 2. WiFi Connection Script (`/opt/device-software/scripts/wifi_connect.py`)
New robust script that handles the complete WiFi connection workflow:

**Teardown Phase:**
- Kills all hostapd/dnsmasq/wpa_supplicant processes (including force kill -9)
- Stops systemd services (hostapd, dnsmasq, wpa_supplicant, systemd-resolved)
- Cleans up PID files
- Flushes wlan0 IP configuration
- Re-enables NetworkManager management of wlan0
- Removes unmanaged device configuration
- Restarts NetworkManager
- Brings wlan0 back up in client mode

**Connection Phase:**
- Scans for WiFi networks
- Deletes existing connection profiles to avoid conflicts
- Attempts connection with nmcli
- Waits for connection establishment (15 attempts, 30 seconds)
- Verifies IP address assignment
- Tests internet connectivity (ping 8.8.8.8)

**Fallback Phase:**
- On failure, automatically restarts AP mode
- Uses wifi_manager.py to restore hotspot

### 3. WiFi Manager Updates (`/opt/device-software/wifi_manager.py` and `/root/wifi_manager.py`)
- Added command-line interface for external script calls
- Supports: `start_hotspot`, `stop_hotspot`, `status`

## Deployment Steps

### On Orange Pi Zero 3:

```bash
# 1. Make scripts executable
chmod +x /opt/device-software/scripts/wifi_connect.py
chmod +x /opt/device-software/wifi_manager.py

# 2. Restart the HTTP server (if running as systemd service)
systemctl restart device-server

# Or if running manually:
pkill -f "python3.*server.py"
cd /opt/device-software/src/http-server
python3 server.py &
```

## Testing

### Test the WiFi connection manually:
```bash
# Run the connection script directly
python3 /opt/device-software/scripts/wifi_connect.py "YourSSID" "YourPassword"

# Check logs
tail -f /opt/device-software/logs/wifi_connect.log
```

### Test via API:
```bash
curl -X POST http://192.168.4.1/setup/wifi \
  -H "Content-Type: application/json" \
  -d '{"ssid": "YourSSID", "password": "YourPassword"}'
```

## Logs to Check

If the first attempt doesn't work, check these logs in order:

1. **WiFi Connection Log** (most important):
   ```bash
   tail -f /opt/device-software/logs/wifi_connect.log
   ```
   Shows: teardown process, connection attempts, errors

2. **HTTP Server Log**:
   ```bash
   tail -f /opt/device-software/logs/http-server.log
   ```
   Shows: API requests, background thread launch

3. **WiFi Manager Log**:
   ```bash
   tail -f /opt/device-software/logs/wifi-manager.log
   ```
   Shows: Hotspot start/stop operations

4. **NetworkManager Log**:
   ```bash
   journalctl -u NetworkManager -f
   ```
   Shows: Network interface changes, connection attempts

5. **System Log**:
   ```bash
   journalctl -f | grep -E "hostapd|dnsmasq|wlan0"
   ```
   Shows: Service starts/stops, errors

## Common Issues and Fixes

### Issue: WiFi connection fails immediately
**Check:**
```bash
nmcli device status
nmcli radio wifi
```
**Fix:**
```bash
nmcli radio wifi on
nmcli device set wlan0 managed yes
```

### Issue: AP mode doesn't tear down
**Check:**
```bash
ps aux | grep -E "hostapd|dnsmasq"
systemctl status hostapd dnsmasq
```
**Fix:**
```bash
pkill -9 -f hostapd
pkill -9 -f dnsmasq
systemctl stop hostapd dnsmasq
```

### Issue: NetworkManager not managing wlan0
**Check:**
```bash
nmcli device show wlan0
cat /etc/NetworkManager/conf.d/99-unmanaged-devices.conf
```
**Fix:**
```bash
rm -f /etc/NetworkManager/conf.d/99-unmanaged-devices.conf
nmcli device set wlan0 managed yes
systemctl restart NetworkManager
```

### Issue: Port 53 already in use (dnsmasq won't stop)
**Check:**
```bash
lsof -i :53
```
**Fix:**
```bash
systemctl stop systemd-resolved
pkill -9 -f dnsmasq
```

### Issue: No IP address after connection
**Check:**
```bash
ip addr show wlan0
nmcli connection show --active
```
**Fix:**
```bash
nmcli connection down "SSID"
nmcli connection up "SSID"
```

## Workflow Summary

```
User sends WiFi credentials via /setup/wifi
    ↓
Server saves credentials to config file
    ↓
Server launches wifi_connect.py in background thread
    ↓
wifi_connect.py tears down AP mode completely
    ↓
wifi_connect.py attempts WiFi connection
    ↓
    ├─ SUCCESS → Verify internet → Done
    └─ FAILURE → Restart AP mode → Client stays on AP
```

## Important Notes

- The API returns immediately (doesn't wait for connection)
- Actual connection happens in background (takes ~30-45 seconds)
- Check logs to see connection progress
- If connection fails, device automatically returns to AP mode
- All services properly stopped/started to avoid conflicts
- NetworkManager regains control of wlan0 for client connections

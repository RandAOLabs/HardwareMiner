# Boot WiFi Connection Debug Guide

## What Should Happen on Fresh Boot (No Credentials)

```
1. start.sh runs
2. Checks if already connected → NO
3. Checks for saved credentials → NOT FOUND
4. Logs: "📡 No saved WiFi credentials found"
5. Falls through to: "📡 Starting hotspot mode..."
6. Searches for wifi_manager.py in multiple locations
7. Finds it and runs: python3 /opt/device-software/wifi_manager.py start_hotspot
8. Hotspot starts with SSID: RNG-Miner-XXXXXXXX
9. HTTP server starts on port 80
```

## What Should Happen on Boot (With Saved Credentials)

```
1. start.sh runs
2. Checks if already connected → NO
3. Checks for saved credentials → FOUND
4. Logs: "🔑 Found saved WiFi credentials, attempting to connect..."
5. Logs: "📡 Attempting to connect to saved network: YourSSID"
6. Tries: nmcli device wifi connect (30s timeout)
7. If SUCCESS:
   - Logs: "✅ Successfully connected to WiFi: YourSSID"
   - Logs: "✅ WiFi connection verified"
   - Skips AP startup
   - Starts HTTP server
8. If FAIL:
   - Logs: "⚠️ Failed to connect to saved WiFi: YourSSID"
   - Falls through to AP mode
   - Starts hotspot
```

## Debug Commands (Run on Orange Pi)

```bash
# 1. Check startup log
tail -50 /var/log/rng-miner/startup.log

# 2. Check if wifi_manager exists
ls -la /opt/device-software/wifi_manager.py
ls -la /opt/rng-miner/wifi_manager.py

# 3. Check if credentials exist
ls -la /opt/device-software/config/wifi_config.json
cat /opt/device-software/config/wifi_config.json

# 4. Check wlan0 state
ip link show wlan0
nmcli device status | grep wlan0

# 5. Check if processes are running
ps aux | grep hostapd
ps aux | grep dnsmasq
ps aux | grep python.*server

# 6. Check systemd service
systemctl status rng-miner.service
journalctl -u rng-miner.service -n 50

# 7. Manually try to start AP
sudo python3 /opt/device-software/wifi_manager.py start_hotspot

# 8. Check NetworkManager
systemctl status NetworkManager
nmcli radio wifi
```

## Common Issues

### Issue: wlan0 in DORMANT state
**Cause**: NetworkManager or wpa_supplicant not managing interface properly
**Fix**:
```bash
sudo nmcli device set wlan0 managed yes
sudo nmcli radio wifi on
sudo systemctl restart NetworkManager
```

### Issue: No logs in /var/log/rng-miner/
**Cause**: start.sh not running or failing early
**Check**:
```bash
# Is the service running?
systemctl status rng-miner.service

# Try running start.sh manually
sudo /opt/rng-miner/start.sh
```

### Issue: wifi_manager.py not found
**Cause**: Not copied during install
**Fix**:
```bash
# Copy manually
sudo cp /opt/rng-miner/wifi_manager.py /opt/device-software/
sudo chmod +x /opt/device-software/wifi_manager.py
```

### Issue: AP starts but no SSID visible
**Cause**: hostapd failed or wrong config
**Check**:
```bash
# Check hostapd status
ps aux | grep hostapd

# Check hostapd config
cat /etc/hostapd/hostapd.conf

# Check logs
tail -50 /opt/device-software/logs/wifi-manager.log
```

## Expected File Locations After Install

```
/opt/rng-miner/
  ├── start.sh              ← Main startup script
  ├── stop.sh
  ├── wifi_manager.py       ← Copied here
  └── start_ap_direct.sh

/opt/device-software/
  ├── wifi_manager.py       ← Also copied here (preferred)
  ├── config/
  │   └── wifi_config.json  ← Created when credentials saved
  ├── logs/
  │   ├── wifi-manager.log
  │   └── wifi_connect.log
  └── src/
      └── http-server/
          └── server.py

/var/log/rng-miner/
  └── startup.log           ← Check this FIRST

/var/lib/rng-miner/
  └── device_id             ← Device ID (8 chars)
```

## If Nothing Works

1. Get all logs:
```bash
sudo cat /var/log/rng-miner/startup.log
sudo cat /opt/device-software/logs/wifi-manager.log
sudo journalctl -u rng-miner.service -n 100
```

2. Check basic networking:
```bash
ip link
nmcli device status
nmcli radio
systemctl status NetworkManager
```

3. Try manual AP start:
```bash
sudo python3 /opt/device-software/wifi_manager.py start_hotspot
```

4. Check if anything is blocking:
```bash
# Check what's managing wlan0
nmcli device show wlan0

# Check for conflicts
ps aux | grep -E "hostapd|dnsmasq|wpa_supplicant"
```

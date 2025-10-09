# WiFi Connection Fix - Technical Summary

## Problem
The `/setup/wifi` endpoint saved credentials but never attempted to connect. After fixing this, the initial implementation failed because of improper service teardown/startup sequencing.

## Root Cause of Failure
**We were racing NetworkManager** - bringing wlan0 up AFTER restarting NetworkManager, causing NM to not detect the interface properly. No SSIDs were found because wlan0 wasn't properly managed.

## Solution: Follow Old-Bad-Way Pattern

### Critical Sequence (Order Matters!)

#### Teardown Phase:
```
1. Stop systemd services (hostapd, dnsmasq) gracefully
   ↓ wait 3 seconds
2. Kill remaining processes with pkill (not -9)
   ↓ wait 2 seconds
3. Flush wlan0 IP addresses
4. Bring wlan0 DOWN
   ↓ wait 2 seconds
5. Bring wlan0 UP ← CRITICAL: Before NM restart!
   ↓ wait 2 seconds
6. Set wlan0 managed by NetworkManager
   ↓ wait 2 seconds
7. Restart NetworkManager
   ↓ wait 5 seconds
8. Start systemd-resolved
   ↓ wait 2 seconds
9. Enable WiFi radio
   ↓ wait 2 seconds
10. Poll "nmcli device status" until wlan0 is ready
    ↓ wait up to 20 seconds (10 checks × 2 sec)
11. Extra buffer wait
    ↓ wait 3 seconds
```

#### Connection Phase:
```
1. Stop hostapd/dnsmasq (ensure they're dead)
   ↓ wait 2 seconds
2. Restart wpa_supplicant (stop → wait → start)
   ↓ wait 5 seconds total
3. Scan for networks
   ↓ wait 5 seconds for scan completion
4. Delete existing connection profile
   ↓ wait 2 seconds
5. Attempt connection with nmcli
6. If fails, try alternative method (nmcli connection add)
7. Poll connection state 6 times × 5 seconds = 30 seconds
8. Verify IP address assigned (and not AP IP)
```

### Key Differences from Failed Attempt:

| What We Did Wrong | What We Fixed |
|-------------------|---------------|
| Brought wlan0 up AFTER NM restart | Brought wlan0 up BEFORE NM restart |
| Stopped systemd-resolved and left it stopped | Start systemd-resolved back up |
| Used `pkill -9` (force kill) | Use graceful `pkill` then systemctl |
| Killed wpa_supplicant during teardown | Restart wpa_supplicant during connection |
| Short waits (1-2 seconds) | Longer waits (3-5 seconds) at critical points |
| No NM readiness check | Poll until NM recognizes wlan0 properly |
| Immediate scan after NM restart | Wait for NM to stabilize, then scan |

### Why Old-Bad-Way Worked

The old-bad-way worked because:
1. **Polling loop gave natural delays** - The 10-60 second main loop gave services time to stabilize
2. **Preserved systemd-resolved** - Started it back up for proper DNS
3. **Proper service restart order** - wpa_supplicant → NetworkManager → connect
4. **Patient waits** - Multiple 5-second waits during connection attempts
5. **Interface up before NM** - Ensured wlan0 was UP before NetworkManager tried to manage it

### Total Time Investment

**Teardown: ~45 seconds**
- Service stops: 3s
- Process kills: 2s
- Interface reset: 2s
- Interface up: 2s
- NM setup: 2s
- NM restart: 5s
- systemd-resolved: 2s
- Radio enable: 2s
- NM stabilization: up to 20s
- Buffer: 3s

**Connection: ~60 seconds**
- Service stops: 2s
- wpa_supplicant restart: 5s
- Network scan: 5s
- Connection delete: 2s
- Connection attempt: ~5s
- Connection polling: 30s
- IP verification: 3s

**Total: ~105 seconds (1 minute 45 seconds)**

This is acceptable for a one-time WiFi setup operation.

## Files Modified

1. `/opt/device-software/scripts/wifi_connect.py` - Complete rewrite of teardown and connection logic
2. `/opt/device-software/src/http-server/server.py` - Triggers wifi_connect.py
3. `/opt/device-software/wifi_manager.py` - Added CLI support for AP restart

## Testing Checklist

On next fresh install test:
- [ ] AP starts properly after boot
- [ ] Can access device via AP (192.168.4.1)
- [ ] Submit WiFi credentials via /setup/wifi
- [ ] Check logs show proper teardown sequence
- [ ] Verify wlan0 comes up (not unavailable/unmanaged)
- [ ] Verify networks are found in scan
- [ ] Verify connection attempt completes
- [ ] If success: device gets IP and has internet
- [ ] If failure: AP restarts and device is accessible again

## Debugging Commands

If it fails again on fresh install, check:
```bash
# Check wlan0 status
ip addr show wlan0
nmcli device status | grep wlan0

# Check services
systemctl status hostapd
systemctl status dnsmasq
systemctl status NetworkManager
systemctl status wpa_supplicant

# Check if NM is managing wlan0
nmcli device show wlan0 | grep GENERAL.MANAGED

# Check WiFi radio
nmcli radio wifi

# Try manual scan
nmcli device wifi rescan
nmcli device wifi list

# Check logs
tail -100 /opt/device-software/logs/wifi_connect.log
journalctl -u NetworkManager -n 50
```

#!/bin/bash
# WiFi Status Check and Diagnostics Script

echo "=========================================="
echo "WiFi Status Diagnostics"
echo "=========================================="
echo ""

echo "--- 1. WLAN0 Interface Status ---"
ip addr show wlan0 2>/dev/null || echo "WLAN0 not found"
echo ""

echo "--- 2. NetworkManager Device Status ---"
nmcli device status | grep wlan0 || echo "WLAN0 not in nmcli"
echo ""

echo "--- 3. NetworkManager Managed Status ---"
nmcli device show wlan0 | grep GENERAL.MANAGED
echo ""

echo "--- 4. Active WiFi Connection ---"
nmcli -t -f ACTIVE,SSID,SIGNAL,SECURITY dev wifi | grep "^yes" || echo "No active WiFi connection"
echo ""

echo "--- 5. Running Services ---"
echo -n "hostapd: "
pgrep -f hostapd > /dev/null && echo "RUNNING (PID: $(pgrep -f hostapd))" || echo "NOT RUNNING"

echo -n "dnsmasq: "
pgrep -f dnsmasq > /dev/null && echo "RUNNING (PID: $(pgrep -f dnsmasq))" || echo "NOT RUNNING"

echo -n "wpa_supplicant: "
pgrep -f "wpa_supplicant.*wlan0" > /dev/null && echo "RUNNING (PID: $(pgrep -f 'wpa_supplicant.*wlan0'))" || echo "NOT RUNNING"
echo ""

echo "--- 6. Port 53 (DNS) Status ---"
lsof -i :53 2>/dev/null | head -5 || echo "Port 53 not in use"
echo ""

echo "--- 7. Current Mode Detection ---"
if pgrep -f hostapd > /dev/null; then
    echo "MODE: AP (Hotspot Mode)"
    echo "SSID: $(grep "^ssid=" /etc/hostapd/hostapd.conf 2>/dev/null | cut -d= -f2)"
    echo "IP: $(ip addr show wlan0 | grep "inet " | awk '{print $2}')"
elif nmcli -t -f ACTIVE,SSID dev wifi | grep -q "^yes"; then
    echo "MODE: CLIENT (Connected to WiFi)"
    SSID=$(nmcli -t -f ACTIVE,SSID dev wifi | grep "^yes" | cut -d: -f2)
    echo "Connected to: $SSID"
    echo "IP: $(ip addr show wlan0 | grep "inet " | awk '{print $2}')"
else
    echo "MODE: UNKNOWN/DISCONNECTED"
fi
echo ""

echo "--- 8. DHCP Leases (if in AP mode) ---"
if [ -f /var/lib/dhcp/dnsmasq.leases ]; then
    cat /var/lib/dhcp/dnsmasq.leases
else
    echo "No DHCP leases file"
fi
echo ""

echo "--- 9. NetworkManager Unmanaged Config ---"
if [ -f /etc/NetworkManager/conf.d/99-unmanaged-devices.conf ]; then
    echo "FOUND (wlan0 is unmanaged):"
    cat /etc/NetworkManager/conf.d/99-unmanaged-devices.conf
else
    echo "NOT FOUND (wlan0 should be managed by NetworkManager)"
fi
echo ""

echo "--- 10. Recent WiFi Connection Log ---"
if [ -f /opt/device-software/logs/wifi_connect.log ]; then
    echo "Last 20 lines:"
    tail -20 /opt/device-software/logs/wifi_connect.log
else
    echo "No wifi_connect.log found"
fi
echo ""

echo "=========================================="
echo "Diagnostics Complete"
echo "=========================================="

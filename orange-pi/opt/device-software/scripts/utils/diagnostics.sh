#!/bin/bash
#
# RNG Miner Diagnostics Script
#
# This script collects all relevant information for debugging
# WiFi hotspot and service issues on Orange Pi
#

set -uo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 RNG Miner Diagnostics Report${NC}"
echo "=================================="
echo "Generated: $(date)"
echo ""

# Function to show status with colors
show_status() {
    local service=$1
    local status=$2
    if [[ "$status" == *"active"* ]]; then
        echo -e "${GREEN}✅ $service: $status${NC}"
    elif [[ "$status" == *"inactive"* ]] || [[ "$status" == *"failed"* ]]; then
        echo -e "${RED}❌ $service: $status${NC}"
    else
        echo -e "${YELLOW}⚠️  $service: $status${NC}"
    fi
}

echo -e "${BLUE}📋 SYSTEM SERVICES STATUS${NC}"
echo "=========================="

# Check systemd services
echo "Core Services:"
for service in rng-miner hostapd dnsmasq NetworkManager systemd-resolved; do
    # Check if service exists (installed) regardless of running state
    if systemctl list-unit-files | grep -q "^$service.service" || [[ -f "/etc/systemd/system/$service.service" ]] || [[ -f "/lib/systemd/system/$service.service" ]]; then
        status=$(systemctl is-active $service 2>/dev/null || echo "inactive")
        show_status "$service" "$status"
    else
        # Double-check by looking for the executable
        case $service in
            hostapd) [[ -f /usr/sbin/hostapd ]] && show_status "$service" "installed-but-inactive" || echo -e "${YELLOW}⚠️  $service: not installed${NC}" ;;
            dnsmasq) [[ -f /usr/sbin/dnsmasq ]] && show_status "$service" "installed-but-inactive" || echo -e "${YELLOW}⚠️  $service: not installed${NC}" ;;
            *) echo -e "${YELLOW}⚠️  $service: not installed${NC}" ;;
        esac
    fi
done

echo ""
echo -e "${BLUE}🌐 NETWORK INTERFACE STATUS${NC}"
echo "============================"

# Check wlan0 status
echo "wlan0 Interface:"
if ip link show wlan0 >/dev/null 2>&1; then
    wlan_status=$(ip link show wlan0 | grep -o "state [A-Z]*" | cut -d' ' -f2)
    if [[ "$wlan_status" == "UP" ]]; then
        echo -e "${GREEN}✅ wlan0 state: $wlan_status${NC}"
    else
        echo -e "${RED}❌ wlan0 state: $wlan_status${NC}"
    fi

    # Check IP address
    if ip addr show wlan0 | grep -q "192.168.4.1"; then
        echo -e "${GREEN}✅ wlan0 IP: 192.168.4.1 assigned${NC}"
    else
        echo -e "${RED}❌ wlan0 IP: 192.168.4.1 NOT assigned${NC}"
        echo "   Current IPs: $(ip addr show wlan0 | grep "inet " | awk '{print $2}' | tr '\n' ' ')"
    fi
else
    echo -e "${RED}❌ wlan0: Interface not found${NC}"
fi

echo ""
echo -e "${BLUE}🔌 PORT AND PROCESS STATUS${NC}"
echo "=========================="

# Check port 53
port53_process=$(ss -tulpn | grep :53 || echo "none")
if [[ "$port53_process" == "none" ]]; then
    echo -e "${GREEN}✅ Port 53: Available${NC}"
else
    echo -e "${YELLOW}⚠️  Port 53: In use${NC}"
    echo "   $port53_process"
fi

# Check rfkill status
echo ""
echo "WiFi Hardware Status:"
rfkill_status=$(rfkill list wlan 2>/dev/null || echo "no wlan devices")
if [[ "$rfkill_status" == "no wlan devices" ]]; then
    echo -e "${RED}❌ WiFi hardware: No devices found${NC}"
else
    if echo "$rfkill_status" | grep -q "Soft blocked: no" && echo "$rfkill_status" | grep -q "Hard blocked: no"; then
        echo -e "${GREEN}✅ WiFi hardware: Not blocked${NC}"
    else
        echo -e "${RED}❌ WiFi hardware: Blocked${NC}"
        echo "$rfkill_status"
    fi
fi

echo ""
echo -e "${BLUE}📝 RECENT SERVICE LOGS${NC}"
echo "====================="

# Show recent logs for failed services
for service in rng-miner hostapd dnsmasq; do
    status=$(systemctl is-active $service 2>/dev/null || echo "inactive")
    if [[ "$status" != "active" ]]; then
        echo ""
        echo -e "${YELLOW}Last 5 log entries for $service:${NC}"
        journalctl -u $service -n 5 --no-pager -q 2>/dev/null || echo "No logs available"
    fi
done

echo ""
echo -e "${BLUE}🔧 CONFIGURATION STATUS${NC}"
echo "======================="

# Check important config files
configs=(
    "/etc/dnsmasq.conf:dnsmasq config"
    "/etc/hostapd/hostapd.conf:hostapd config"
    "/var/lib/rng-miner/device_id:device ID"
    "/etc/systemd/system/dnsmasq.service.d/99-no-dbus.conf:dnsmasq D-Bus override"
)

for config_item in "${configs[@]}"; do
    IFS=':' read -r file desc <<< "$config_item"
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $desc: Present${NC}"
    else
        echo -e "${RED}❌ $desc: Missing${NC}"
    fi
done

echo ""
echo -e "${BLUE}🐍 HTTP SERVER STATUS${NC}"
echo "====================="

# Check server file location
SERVER_SCRIPT="/opt/device-software/src/http-server/server.py"
if [[ -f "$SERVER_SCRIPT" ]]; then
    echo -e "${GREEN}✅ Server script: Found at $SERVER_SCRIPT${NC}"

    # Check if server is running
    if pgrep -f "$SERVER_SCRIPT" > /dev/null; then
        echo -e "${GREEN}✅ Server process: Running${NC}"
        server_pid=$(pgrep -f "$SERVER_SCRIPT")
        echo "   PID: $server_pid"
    else
        echo -e "${RED}❌ Server process: Not running${NC}"
    fi

    # Check port 80
    if ss -tulpn | grep -q ":80 "; then
        echo -e "${GREEN}✅ Port 80: In use (server should be listening)${NC}"
        ss -tulpn | grep ":80 " | head -1
    else
        echo -e "${RED}❌ Port 80: Not in use (server not listening)${NC}"
    fi

    # Test if we can import the server module
    echo ""
    echo "Testing Python dependencies..."
    if python3 -c "import sys; sys.path.insert(0, '/opt/device-software/src/http-server'); from pathlib import Path; from flask import Flask; from flask_cors import CORS; print('✅ All Python dependencies available')" 2>/dev/null; then
        echo -e "${GREEN}✅ Python dependencies: OK${NC}"
    else
        echo -e "${RED}❌ Python dependencies: Missing modules${NC}"
        echo "   Try: pip3 install flask flask-cors"
    fi
else
    echo -e "${RED}❌ Server script: NOT FOUND at $SERVER_SCRIPT${NC}"
    echo "   Expected location: $SERVER_SCRIPT"
    echo "   Searching for server.py files..."
    find /opt -name "server.py" 2>/dev/null | head -5 || echo "   No server.py files found"
fi

# Check startup script
echo ""
echo "Startup Configuration:"
START_SCRIPT="/opt/rng-miner/start.sh"
if [[ -f "$START_SCRIPT" ]]; then
    echo -e "${GREEN}✅ Start script: Found${NC}"

    # Check if start.sh references the correct server path
    if grep -q "/opt/device-software/src/http-server/server.py" "$START_SCRIPT"; then
        echo -e "${GREEN}✅ Start script points to correct server location${NC}"
    else
        echo -e "${RED}❌ Start script has wrong server path${NC}"
        echo "   Current server reference in start.sh:"
        grep "server.py" "$START_SCRIPT" | head -3
    fi
else
    echo -e "${RED}❌ Start script: Not found at $START_SCRIPT${NC}"
fi

# Check for recent startup errors
echo ""
echo "Recent startup logs:"
if [[ -f "/var/log/rng-miner/startup.log" ]]; then
    echo "Last 5 lines from startup.log:"
    tail -5 /var/log/rng-miner/startup.log 2>/dev/null || echo "Cannot read startup.log"
else
    echo -e "${YELLOW}⚠️  No startup.log found${NC}"
fi

echo ""
echo -e "${BLUE}🔍 NETWORK MANAGER STATUS${NC}"
echo "========================="

if command -v nmcli >/dev/null 2>&1; then
    nm_status=$(systemctl is-active NetworkManager 2>/dev/null || echo "inactive")
    show_status "NetworkManager" "$nm_status"

    if [[ "$nm_status" == "active" ]]; then
        echo "NetworkManager device status:"
        nmcli device status 2>/dev/null | grep -E "(DEVICE|wlan0)" || echo "No wlan0 in NetworkManager"
    fi
else
    echo -e "${YELLOW}⚠️  nmcli: Not available${NC}"
fi

echo ""
echo -e "${BLUE}📊 QUICK SUMMARY${NC}"
echo "================"

# Count issues
issues=0

# Check critical components
if ! systemctl is-active rng-miner >/dev/null 2>&1; then
    echo -e "${RED}❌ RNG Miner service not running${NC}"
    ((issues++))
fi

if ! systemctl is-active hostapd >/dev/null 2>&1; then
    echo -e "${RED}❌ hostapd service not running${NC}"
    ((issues++))
fi

if ! systemctl is-active dnsmasq >/dev/null 2>&1; then
    echo -e "${RED}❌ dnsmasq service not running${NC}"
    ((issues++))
fi

if ! ip link show wlan0 2>/dev/null | grep -q "state UP"; then
    echo -e "${RED}❌ wlan0 interface not UP${NC}"
    ((issues++))
fi

if ! ip addr show wlan0 2>/dev/null | grep -q "192.168.4.1"; then
    echo -e "${RED}❌ wlan0 missing IP address${NC}"
    ((issues++))
fi

if [[ $issues -eq 0 ]]; then
    echo -e "${GREEN}🎉 All systems appear to be working!${NC}"
    echo "Try connecting to WiFi: RNG-Miner-$(cat /var/lib/rng-miner/device_id 2>/dev/null || echo 'UNKNOWN')"
    echo "Password: RNG-Miner-Password-123"
else
    echo -e "${RED}Found $issues issue(s) that need attention${NC}"
fi

echo ""
echo -e "${BLUE}💡 MANUAL TESTS TO TRY${NC}"
echo "====================="
echo "1. Test HTTP server manually:"
echo "   sudo python3 /opt/device-software/src/http-server/server.py"
echo ""
echo "2. Check if server can bind to port 80:"
echo "   sudo lsof -i :80"
echo "   sudo ss -tulpn | grep :80"
echo ""
echo "3. Test dnsmasq configuration:"
echo "   sudo dnsmasq --test --conf-file=/etc/dnsmasq.conf"
echo ""
echo "4. Manual dnsmasq start (direct method):"
echo "   sudo systemctl stop systemd-resolved"
echo "   sudo pkill dnsmasq"
echo "   sudo dnsmasq --interface=wlan0 --bind-interfaces --listen-address=192.168.4.1 --conf-file=/etc/dnsmasq.conf --keep-in-foreground"
echo ""
echo "5. Manual hostapd start:"
echo "   sudo pkill hostapd"
echo "   sudo hostapd -B /etc/hostapd/hostapd.conf"
echo ""
echo "6. Manual WiFi interface setup:"
echo "   sudo systemctl stop NetworkManager"
echo "   sudo ip link set wlan0 down"
echo "   sudo ip addr flush dev wlan0"
echo "   sudo ip link set wlan0 up"
echo "   sudo ip addr add 192.168.4.1/24 dev wlan0"
echo ""
echo "7. Full manual WiFi hotspot test:"
echo "   cd /opt/rng-miner && source venv/bin/activate"
echo "   python3 -c \"from wifi_manager import WiFiManager; WiFiManager().start_hotspot()\""
echo ""
echo "8. Check process status:"
echo "   ps aux | grep -E '(server.py|dnsmasq|hostapd)'"
echo "   ss -tulpn | grep -E '(:53|:80)'"
echo ""
echo "9. Check detailed logs:"
echo "   sudo journalctl -u rng-miner -n 50 --no-pager"
echo "   tail -20 /var/log/rng-miner/startup.log"
echo "   tail -20 /opt/device-software/logs/http-server.log"
echo ""
echo -e "${YELLOW}🔧 QUICK RESET COMMANDS${NC}"
echo "======================"
echo "If services are stuck, run these to reset:"
echo "   sudo pkill -f 'dnsmasq|hostapd'"
echo "   sudo systemctl stop systemd-resolved"
echo "   sudo systemctl restart rng-miner"

echo ""
echo "Diagnostics complete!"
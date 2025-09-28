#!/bin/bash
#
# Stop RNG Miner services with comprehensive cleanup
#

set -uo pipefail

INSTALL_DIR="/opt/rng-miner"
LOG_DIR="/var/log/rng-miner"
LOG_FILE="$LOG_DIR/startup.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🛑 Stopping RNG Miner services..."

# Kill HTTP server
if [[ -f /var/run/rng-miner.pid ]]; then
    PID=$(cat /var/run/rng-miner.pid)
    if kill "$PID" 2>/dev/null; then
        log "✅ HTTP server stopped (PID: $PID)"
    else
        log "⚠️ HTTP server was not running"
    fi
    rm -f /var/run/rng-miner.pid
fi

# Kill any remaining server processes
pkill -f "python.*server.py" 2>/dev/null && log "🔄 Cleaned up remaining server processes" || true

# Stop direct AP script if running
if [[ -f /var/run/rng-miner-ap.pid ]]; then
    AP_PID=$(cat /var/run/rng-miner-ap.pid)
    if kill "$AP_PID" 2>/dev/null; then
        log "✅ Direct AP script stopped (PID: $AP_PID)"
    else
        log "⚠️ Direct AP script was not running"
    fi
    rm -f /var/run/rng-miner-ap.pid
fi

# Stop WiFi hotspot using Python manager
if [[ -d "$INSTALL_DIR" ]] && [[ -f "$INSTALL_DIR/wifi_manager.py" ]]; then
    cd "$INSTALL_DIR"

    # Try to activate virtual environment
    if [[ -f venv/bin/activate ]]; then
        source venv/bin/activate 2>/dev/null || true
    fi

    python3 -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
try:
    from wifi_manager import WiFiManager
    wifi_manager = WiFiManager()
    wifi_manager.stop_hotspot()
    print('SUCCESS: WiFi hotspot stopped via Python manager')
except Exception as e:
    print(f'WARNING: WiFi manager stop failed: {e}')
" 2>/dev/null && log "✅ WiFi hotspot stopped via Python manager" || log "⚠️ Python WiFi manager stop failed"
fi

# Comprehensive AP service cleanup
log "🔄 Performing comprehensive AP cleanup..."

# Stop systemd services
systemctl stop hostapd 2>/dev/null && log "📡 hostapd service stopped" || true
systemctl stop dnsmasq 2>/dev/null && log "🌐 dnsmasq service stopped" || true

# Kill any remaining processes
pkill -f hostapd 2>/dev/null && log "🔄 Killed remaining hostapd processes" || true
pkill -f dnsmasq 2>/dev/null && log "🔄 Killed remaining dnsmasq processes" || true
pkill -f "start_ap_direct.sh" 2>/dev/null && log "🔄 Killed direct AP scripts" || true

# Reset wlan0 interface
INTERFACE="wlan0"
if ip link show $INTERFACE >/dev/null 2>&1; then
    log "🔄 Resetting $INTERFACE interface..."

    # Flush IP addresses
    ip addr flush dev $INTERFACE 2>/dev/null || true

    # Bring interface down and up
    ip link set dev $INTERFACE down 2>/dev/null || true
    sleep 1
    ip link set dev $INTERFACE up 2>/dev/null || true

    # Re-enable NetworkManager management
    if command -v nmcli >/dev/null 2>&1; then
        nmcli device set $INTERFACE managed yes 2>/dev/null && log "📶 NetworkManager management re-enabled for $INTERFACE" || true
    fi

    log "✅ Interface $INTERFACE reset"
else
    log "⚠️ Interface $INTERFACE not found"
fi

# Restart systemd-resolved if needed
systemctl start systemd-resolved 2>/dev/null && log "🌐 systemd-resolved restarted" || true

log "✅ RNG Miner services stopped and cleaned up"
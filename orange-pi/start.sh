#!/bin/bash
#
# Start RNG Miner services with robust AP startup
#

set -euo pipefail

INSTALL_DIR="/opt/rng-miner"
LOG_DIR="/var/log/rng-miner"
LOG_FILE="$LOG_DIR/startup.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

log "🚀 Starting RNG Miner services..."

cd "$INSTALL_DIR" || error_exit "Could not change to install directory"

# Activate Python environment
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    log "✅ Python virtual environment activated"
else
    log "⚠️ Virtual environment not found, using system Python"
fi

# Check if we need to start hotspot (no existing WiFi connection)
log "🔍 Checking network status..."
WIFI_CONNECTED=false

# Check if connected to WiFi
if command -v nmcli >/dev/null 2>&1; then
    if nmcli -t -f ACTIVE,SSID dev wifi | grep -q '^yes'; then
        WIFI_CONNECTED=true
        CONNECTED_SSID=$(nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes' | cut -d':' -f2)
        log "📶 Already connected to WiFi: $CONNECTED_SSID"
    fi
fi

# Start WiFi hotspot only if not connected to WiFi
if [[ "$WIFI_CONNECTED" == "false" ]]; then
    log "📡 No WiFi connection detected, starting hotspot..."

    # Try Python WiFi manager first
    if python3 -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from wifi_manager import WiFiManager
wifi_manager = WiFiManager()
try:
    wifi_manager.start_hotspot()
    print('SUCCESS: WiFi hotspot started via Python WiFi manager')
    exit(0)
except Exception as e:
    print(f'FAILED: WiFi manager error: {e}')
    exit(1)
"; then
        log "✅ WiFi hotspot started successfully via Python manager"
    else
        log "⚠️ Python WiFi manager failed, trying direct AP script..."

        # Fallback to direct AP script
        if [[ -f "$INSTALL_DIR/start_ap_direct.sh" ]]; then
            chmod +x "$INSTALL_DIR/start_ap_direct.sh"

            # Start AP in background
            "$INSTALL_DIR/start_ap_direct.sh" &
            AP_PID=$!

            # Give it time to start
            sleep 10

            # Check if it's still running
            if kill -0 $AP_PID 2>/dev/null; then
                log "✅ Direct AP script started successfully"
                echo $AP_PID > /var/run/rng-miner-ap.pid
            else
                log "❌ Direct AP script failed to start"
            fi
        else
            log "❌ Direct AP script not found"
        fi
    fi
else
    log "📶 Connected to WiFi, skipping hotspot startup"
fi

# Start HTTP server
log "🌐 Starting HTTP server on port 80..."

# Server location
SERVER_SCRIPT="/opt/device-software/src/http-server/server.py"

# Verify server file exists
if [[ ! -f "$SERVER_SCRIPT" ]]; then
    error_exit "Server script not found at: $SERVER_SCRIPT"
fi

# Check if port 80 is already in use
if ss -tulpn | grep -q ":80 "; then
    log "⚠️ Port 80 is already in use, attempting to stop existing server..."
    pkill -f "python.*server.py" 2>/dev/null || true
    sleep 2
fi

# Start the HTTP server in background
python3 "$SERVER_SCRIPT" &
SERVER_PID=$!

# Save PID
echo $SERVER_PID > /var/run/rng-miner.pid

# Give server time to start
sleep 3

# Verify server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    log "✅ HTTP server started successfully (PID: $SERVER_PID)"

    # Display connection info
    DEVICE_ID=$(cat /var/lib/rng-miner/device_id 2>/dev/null || echo "UNKNOWN")

    if [[ "$WIFI_CONNECTED" == "false" ]]; then
        log "📱 Connect to WiFi: RNG-Miner-${DEVICE_ID}"
        log "🔗 Setup URL: http://192.168.4.1"
    else
        LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}' 2>/dev/null || echo "unknown")
        log "🔗 Server URL: http://${LOCAL_IP}"
    fi
else
    error_exit "HTTP server failed to start"
fi

log "✅ RNG Miner services startup completed"
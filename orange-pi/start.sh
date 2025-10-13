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

# If not connected, check if we have saved credentials and try to connect
if [[ "$WIFI_CONNECTED" == "false" ]]; then
    WIFI_CONFIG_FILE="/opt/device-software/config/wifi_config.json"

    if [[ -f "$WIFI_CONFIG_FILE" ]]; then
        log "🔑 Found saved WiFi credentials, attempting to connect..."

        # Extract SSID and password from config
        if command -v python3 >/dev/null 2>&1; then
            SAVED_SSID=$(python3 -c "import json; print(json.load(open('$WIFI_CONFIG_FILE')).get('ssid', ''))" 2>/dev/null || echo "")
            SAVED_PASSWORD=$(python3 -c "import json; print(json.load(open('$WIFI_CONFIG_FILE')).get('password', ''))" 2>/dev/null || echo "")

            if [[ -n "$SAVED_SSID" ]]; then
                log "📡 Attempting to connect to saved network: $SAVED_SSID"

                # Ensure WiFi radio is on
                nmcli radio wifi on 2>/dev/null || true
                sleep 2

                # Attempt connection with timeout
                if timeout 30s nmcli device wifi connect "$SAVED_SSID" password "$SAVED_PASSWORD" 2>/dev/null; then
                    log "✅ Successfully connected to WiFi: $SAVED_SSID"
                    WIFI_CONNECTED=true

                    # Wait for connection to stabilize
                    sleep 5

                    # Verify connection
                    if nmcli -t -f ACTIVE,SSID dev wifi | grep -q '^yes'; then
                        log "✅ WiFi connection verified"
                    else
                        log "⚠️ Connection verification failed, will start AP"
                        WIFI_CONNECTED=false
                    fi
                else
                    log "⚠️ Failed to connect to saved WiFi: $SAVED_SSID"
                    log "📡 Will start hotspot mode instead"
                fi
            fi
        fi
    else
        log "📡 No saved WiFi credentials found"
    fi
fi

# Start WiFi hotspot only if not connected to WiFi
if [[ "$WIFI_CONNECTED" == "false" ]]; then
    log "📡 Starting hotspot mode..."

    # Try to find wifi_manager.py in multiple locations
    WIFI_MANAGER_SCRIPT=""
    for path in "$INSTALL_DIR/wifi_manager.py" "/opt/device-software/wifi_manager.py" "/opt/device-software/src/wifi-manager/wifi_manager.py"; do
        if [[ -f "$path" ]]; then
            WIFI_MANAGER_SCRIPT="$path"
            log "Found wifi_manager at: $path"
            break
        fi
    done

    # Try Python WiFi manager first
    if [[ -n "$WIFI_MANAGER_SCRIPT" ]]; then
        log "Attempting to start hotspot via Python WiFi manager..."
        if python3 "$WIFI_MANAGER_SCRIPT" start_hotspot 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ WiFi hotspot started successfully via Python manager"
        else
            log "⚠️ Python WiFi manager failed (exit code: $?)"
        fi
    else
        log "⚠️ WiFi manager script not found, trying direct AP script..."

        # Fallback to direct AP script
        if [[ -f "$INSTALL_DIR/start_ap_direct.sh" ]]; then
            chmod +x "$INSTALL_DIR/start_ap_direct.sh"

            log "Starting AP via direct script..."
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
            log "❌ Direct AP script not found at: $INSTALL_DIR/start_ap_direct.sh"
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
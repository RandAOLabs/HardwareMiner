#!/bin/bash
# Orange Pi Device Software Startup Script
# Boot-time initialization for HTTP server and device services

set -euo pipefail

# Configuration
DEVICE_SOFTWARE_PATH="/opt/device-software"
HTTP_SERVER_PATH="$DEVICE_SOFTWARE_PATH/src/http-server"
LOG_FILE="$DEVICE_SOFTWARE_PATH/logs/startup.log"
PID_FILE="$DEVICE_SOFTWARE_PATH/config/http-server.pid"

# Logging function
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Create necessary directories
create_directories() {
    log_message "Creating directory structure..."
    mkdir -p "$DEVICE_SOFTWARE_PATH/logs"
    mkdir -p "$DEVICE_SOFTWARE_PATH/config"
    mkdir -p "$DEVICE_SOFTWARE_PATH/tests"
}

# Install Python dependencies
install_dependencies() {
    log_message "Installing Python dependencies..."
    if [ -f "$HTTP_SERVER_PATH/requirements.txt" ]; then
        pip3 install -r "$HTTP_SERVER_PATH/requirements.txt" >> "$LOG_FILE" 2>&1
        log_message "Dependencies installed successfully"
    else
        log_message "WARNING: requirements.txt not found"
    fi
}

# Check if HTTP server is already running
check_server_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_message "HTTP server already running with PID $pid"
            return 0
        else
            log_message "Stale PID file found, removing..."
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Start WiFi hotspot
start_wifi_hotspot() {
    log_message "Starting WiFi hotspot..."

    # Use the start-hotspot script
    if "$DEVICE_SOFTWARE_PATH/scripts/start-hotspot.sh"; then
        log_message "WiFi hotspot started successfully"
        return 0
    else
        log_message "ERROR: WiFi hotspot failed to start"
        return 1
    fi
}

# Start HTTP server
start_http_server() {
    log_message "Starting HTTP server..."

    cd "$HTTP_SERVER_PATH"

    # Start server in background
    nohup python3 server.py >> "$LOG_FILE" 2>&1 &
    local server_pid=$!

    # Save PID
    echo "$server_pid" > "$PID_FILE"

    # Wait a moment and check if server started successfully
    sleep 3
    if ps -p "$server_pid" > /dev/null 2>&1; then
        log_message "HTTP server started successfully with PID $server_pid"
        return 0
    else
        log_message "ERROR: HTTP server failed to start"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Stop HTTP server
stop_http_server() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        log_message "Stopping HTTP server (PID: $pid)..."

        if ps -p "$pid" > /dev/null 2>&1; then
            kill -TERM "$pid"

            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done

            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                log_message "Force killing HTTP server..."
                kill -KILL "$pid"
            fi

            log_message "HTTP server stopped"
        fi

        rm -f "$PID_FILE"
    else
        log_message "HTTP server PID file not found"
    fi
}

# Restart HTTP server
restart_http_server() {
    log_message "Restarting HTTP server..."
    stop_http_server
    sleep 2
    start_http_server
}

# Wait for network interface to be ready
wait_for_network() {
    local max_attempts=30
    local attempt=1

    log_message "Waiting for network interface to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if ip addr show wlan0 | grep "192.168.4.1" > /dev/null 2>&1; then
            log_message "✅ Network interface ready (192.168.4.1 assigned)"
            return 0
        fi

        log_message "Attempt $attempt/$max_attempts: Waiting for network interface..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_message "⚠️ Network interface not ready after $max_attempts attempts"
    return 1
}

# Test server accessibility
test_server_startup() {
    log_message "Testing server accessibility..."

    # Wait a moment for server to fully start
    sleep 5

    # Test localhost access
    if curl -s -m 5 http://localhost/health > /dev/null 2>&1; then
        log_message "✅ HTTP server accessible on localhost"
    else
        log_message "⚠️ HTTP server not accessible on localhost"
    fi

    # Test network access
    if curl -s -m 5 http://192.168.4.1/health > /dev/null 2>&1; then
        log_message "✅ HTTP server accessible on hotspot network"
    else
        log_message "⚠️ HTTP server not accessible on hotspot network"
    fi
}

# Main startup function
startup() {
    log_message "Orange Pi Device Software starting up..."

    create_directories
    install_dependencies

    # Start WiFi hotspot first
    if start_wifi_hotspot; then
        # Wait for network to be properly configured
        wait_for_network
    else
        log_message "ERROR: WiFi hotspot failed to start - continuing anyway"
    fi

    # Then start HTTP server
    if ! check_server_status; then
        if start_http_server; then
            # Test server accessibility
            test_server_startup
        else
            log_message "ERROR: HTTP server failed to start"
            exit 1
        fi
    fi

    log_message "🎉 Startup complete - device ready for mobile app connection"
    log_message "📱 Look for WiFi network starting with 'RNG-Miner-'"
    log_message "🔗 Test connectivity with: /opt/device-software/scripts/test-server.sh"
    log_message "📱 Mobile app should connect to: http://192.168.4.1/health"
}

# Main script logic
case "${1:-startup}" in
    "startup")
        startup
        ;;
    "start")
        start_http_server
        ;;
    "stop")
        stop_http_server
        ;;
    "restart")
        restart_http_server
        ;;
    "status")
        if check_server_status; then
            echo "HTTP server is running"
            exit 0
        else
            echo "HTTP server is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {startup|start|stop|restart|status}"
        exit 1
        ;;
esac
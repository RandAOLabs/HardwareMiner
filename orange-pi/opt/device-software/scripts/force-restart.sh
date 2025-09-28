#!/bin/bash
# Orange Pi Complete Service Restart Script
# Forcefully restart all services to ensure clean state

set -euo pipefail

LOG_FILE="/opt/device-software/logs/force-restart.log"

log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Kill all existing processes
kill_all_processes() {
    log_message "🔴 Killing all existing processes..."

    # Kill HTTP server
    pkill -f "server.py" || true
    pkill -f "http-server" || true

    # Kill WiFi processes
    pkill -f "hostapd" || true
    pkill -f "dnsmasq" || true

    # Kill WiFi manager
    pkill -f "wifi_manager.py" || true

    log_message "All processes killed"
}

# Reset network interface
reset_network() {
    log_message "🔄 Resetting network interface..."

    # Bring down interface
    ip link set wlan0 down || true

    # Flush IP addresses
    ip addr flush dev wlan0 || true

    # Wait a moment
    sleep 2

    log_message "Network interface reset"
}

# Clear firewall rules
reset_firewall() {
    log_message "🧱 Resetting firewall rules..."

    # Remove our specific rules
    iptables -D INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null || true
    iptables -D INPUT -s 192.168.4.0/24 -j ACCEPT 2>/dev/null || true
    iptables -D INPUT -s 192.168.12.0/24 -j ACCEPT 2>/dev/null || true

    log_message "Firewall rules reset"
}

# Start WiFi hotspot
start_wifi() {
    log_message "📡 Starting WiFi hotspot..."

    cd /opt/device-software/src/wifi-manager
    python3 wifi_manager.py start

    if [ $? -eq 0 ]; then
        log_message "✅ WiFi hotspot started"
        return 0
    else
        log_message "❌ WiFi hotspot failed to start"
        return 1
    fi
}

# Wait for network interface
wait_for_interface() {
    log_message "⏳ Waiting for network interface..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if ip addr show wlan0 | grep "192.168.4.1" > /dev/null 2>&1; then
            log_message "✅ Network interface ready (192.168.4.1)"
            return 0
        fi

        log_message "Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_message "❌ Network interface not ready after $max_attempts attempts"
    return 1
}

# Start HTTP server
start_http_server() {
    log_message "🚀 Starting HTTP server..."

    cd /opt/device-software/src/http-server
    nohup python3 server.py >> "$LOG_FILE" 2>&1 &
    local server_pid=$!

    # Save PID
    echo "$server_pid" > /opt/device-software/config/http-server.pid

    # Wait and verify
    sleep 5
    if ps -p "$server_pid" > /dev/null 2>&1; then
        log_message "✅ HTTP server started (PID: $server_pid)"
        return 0
    else
        log_message "❌ HTTP server failed to start"
        return 1
    fi
}

# Test endpoints
test_endpoints() {
    log_message "🔍 Testing endpoints..."

    # Wait for server to fully initialize
    sleep 10

    # Test localhost
    if curl -s -m 5 http://localhost/health > /dev/null 2>&1; then
        log_message "✅ localhost/health - OK"
        local response=$(curl -s -m 5 http://localhost/health)
        log_message "Response: $response"
    else
        log_message "❌ localhost/health - FAILED"
    fi

    # Test hotspot IP
    if curl -s -m 5 http://192.168.4.1/health > /dev/null 2>&1; then
        log_message "✅ 192.168.4.1/health - OK"
        local response=$(curl -s -m 5 http://192.168.4.1/health)
        log_message "Response: $response"
    else
        log_message "❌ 192.168.4.1/health - FAILED"
    fi

    # Test device info
    if curl -s -m 5 http://192.168.4.1/device/info > /dev/null 2>&1; then
        log_message "✅ 192.168.4.1/device/info - OK"
    else
        log_message "❌ 192.168.4.1/device/info - FAILED"
    fi
}

# Show status
show_status() {
    log_message "📊 System Status:"

    # Network interface
    local ip_info=$(ip addr show wlan0 | grep "inet " | head -1)
    log_message "Network: $ip_info"

    # Processes
    local hostapd_status=$(pgrep -f hostapd > /dev/null && echo "RUNNING" || echo "NOT RUNNING")
    local dnsmasq_status=$(pgrep -f dnsmasq > /dev/null && echo "RUNNING" || echo "NOT RUNNING")
    local server_status=$(pgrep -f server.py > /dev/null && echo "RUNNING" || echo "NOT RUNNING")

    log_message "hostapd: $hostapd_status"
    log_message "dnsmasq: $dnsmasq_status"
    log_message "HTTP server: $server_status"

    # Port status
    local port_status=$(netstat -tln | grep ":80 " > /dev/null && echo "LISTENING" || echo "NOT LISTENING")
    log_message "Port 80: $port_status"
}

# Main function
main() {
    log_message "🔄 Orange Pi Force Restart Starting..."

    # Step 1: Kill everything
    kill_all_processes

    # Step 2: Reset network
    reset_network
    reset_firewall

    # Step 3: Start services
    if start_wifi; then
        if wait_for_interface; then
            if start_http_server; then
                test_endpoints
                show_status
                log_message "🎉 Force restart completed successfully!"
                log_message "📱 Mobile app can now connect to RNG-Miner WiFi network"
                log_message "🔗 Test with: curl http://192.168.4.1/health"
            else
                log_message "💥 HTTP server startup failed"
                exit 1
            fi
        else
            log_message "💥 Network interface setup failed"
            exit 1
        fi
    else
        log_message "💥 WiFi hotspot startup failed"
        exit 1
    fi
}

# Run main function
main
#!/bin/bash
# Orange Pi HTTP Server Testing Script
# Test server accessibility and endpoints

set -euo pipefail

# Configuration
LOG_FILE="/opt/device-software/logs/test-server.log"

# Logging function
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Test network interface configuration
test_network_interface() {
    log_message "=== Testing Network Interface Configuration ==="

    # Check if wlan0 exists
    if ip link show wlan0 >/dev/null 2>&1; then
        log_message "✅ wlan0 interface exists"

        # Check IP configuration
        local ip_info=$(ip addr show wlan0 | grep "inet ")
        if echo "$ip_info" | grep -q "192.168.4.1"; then
            log_message "✅ wlan0 has correct IP (192.168.4.1)"
        else
            log_message "❌ wlan0 missing correct IP address"
            log_message "Current wlan0 config: $ip_info"
        fi
    else
        log_message "❌ wlan0 interface not found"
    fi

    # Test interface connectivity
    log_message "Testing interface connectivity..."
    if ping -c 1 -W 2 192.168.4.1 >/dev/null 2>&1; then
        log_message "✅ 192.168.4.1 is reachable via ping"
    else
        log_message "⚠️  192.168.4.1 not responding to ping"
    fi
}

# Test HTTP server process
test_server_process() {
    log_message "=== Testing HTTP Server Process ==="

    # Check if Python HTTP server is running
    if pgrep -f "server.py" >/dev/null; then
        local pid=$(pgrep -f "server.py")
        log_message "✅ HTTP server process running (PID: $pid)"
    else
        log_message "❌ HTTP server process not found"
    fi

    # Check if port 80 is listening
    if netstat -tln | grep ":80 " >/dev/null 2>&1; then
        log_message "✅ Port 80 is listening"
        netstat -tln | grep ":80" | head -1 | log_message "Port info: $(cat)"
    else
        log_message "❌ Port 80 is not listening"
    fi
}

# Test HTTP endpoints
test_http_endpoints() {
    log_message "=== Testing HTTP Endpoints ==="

    # Test localhost access
    log_message "Testing localhost access..."
    if curl -s -m 5 http://localhost/health >/dev/null 2>&1; then
        log_message "✅ localhost/health accessible"
        local response=$(curl -s -m 5 http://localhost/health)
        log_message "Response: $response"
    else
        log_message "❌ localhost/health not accessible"
    fi

    # Test 192.168.4.1 access
    log_message "Testing 192.168.4.1 access..."
    if curl -s -m 5 http://192.168.4.1/health >/dev/null 2>&1; then
        log_message "✅ 192.168.4.1/health accessible"
        local response=$(curl -s -m 5 http://192.168.4.1/health)
        log_message "Response: $response"
    else
        log_message "❌ 192.168.4.1/health not accessible"
    fi

    # Test device info endpoint
    log_message "Testing device info endpoint..."
    if curl -s -m 5 http://192.168.4.1/device/info >/dev/null 2>&1; then
        log_message "✅ /device/info endpoint accessible"
        local device_info=$(curl -s -m 5 http://192.168.4.1/device/info)
        log_message "Device info: $device_info"
    else
        log_message "❌ /device/info endpoint not accessible"
    fi
}

# Test from external client perspective
test_external_access() {
    log_message "=== Testing External Access Simulation ==="

    # Simulate what a mobile client would try
    log_message "Simulating mobile client access patterns..."

    # Test with different User-Agent
    local user_agent="ReactNative/0.72 CFNetwork/1408.0.4 Darwin/22.5.0"

    if curl -s -m 5 -H "User-Agent: $user_agent" http://192.168.4.1/health >/dev/null 2>&1; then
        log_message "✅ Mobile client simulation successful"
    else
        log_message "❌ Mobile client simulation failed"
    fi

    # Test with CORS preflight request
    if curl -s -m 5 -X OPTIONS -H "Access-Control-Request-Method: GET" http://192.168.4.1/health >/dev/null 2>&1; then
        log_message "✅ CORS preflight request successful"
    else
        log_message "⚠️  CORS preflight request failed (may be normal)"
    fi
}

# Test firewall configuration
test_firewall() {
    log_message "=== Testing Firewall Configuration ==="

    # Check iptables rules
    if iptables -L INPUT | grep "80" >/dev/null 2>&1; then
        log_message "✅ Firewall rules for port 80 found"
    else
        log_message "⚠️  No specific firewall rules for port 80"
    fi

    # Check if hotspot network is allowed
    if iptables -L INPUT | grep "192.168.4.0/24" >/dev/null 2>&1; then
        log_message "✅ Firewall allows hotspot network traffic"
    else
        log_message "⚠️  No specific firewall rules for hotspot network"
    fi
}

# Generate connectivity report
generate_report() {
    log_message "=== Connectivity Test Report ==="
    log_message "Test completed at: $(date)"
    log_message "Log file location: $LOG_FILE"
    log_message ""
    log_message "For mobile app testing, use these commands:"
    log_message "curl http://192.168.4.1/health"
    log_message "curl http://192.168.4.1/device/info"
    log_message ""
    log_message "If tests fail, check:"
    log_message "1. WiFi hotspot is running: python3 /opt/device-software/src/wifi-manager/wifi_manager.py status"
    log_message "2. HTTP server is running: ps aux | grep server.py"
    log_message "3. Firewall is not blocking: sudo iptables -L INPUT"
    log_message "4. Interface configuration: ip addr show wlan0"
}

# Main execution
main() {
    log_message "Orange Pi HTTP Server Connectivity Test Starting..."

    test_network_interface
    test_server_process
    test_http_endpoints
    test_external_access
    test_firewall
    generate_report

    log_message "Connectivity test completed!"
}

# Handle script arguments
case "${1:-test}" in
    "test")
        main
        ;;
    "quick")
        test_http_endpoints
        ;;
    "network")
        test_network_interface
        ;;
    *)
        echo "Usage: $0 {test|quick|network}"
        echo "  test    - Run full connectivity test (default)"
        echo "  quick   - Test HTTP endpoints only"
        echo "  network - Test network interface only"
        exit 1
        ;;
esac
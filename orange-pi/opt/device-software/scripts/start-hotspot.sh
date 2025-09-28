#!/bin/bash
# Orange Pi WiFi Hotspot Startup Script
# Start WiFi hotspot with DHCP service

set -euo pipefail

# Configuration
DEVICE_SOFTWARE_PATH="/opt/device-software"
WIFI_MANAGER_PATH="$DEVICE_SOFTWARE_PATH/src/wifi-manager"
LOG_FILE="$DEVICE_SOFTWARE_PATH/logs/wifi-manager.log"

# Logging function
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Install required packages
install_dependencies() {
    log_message "Checking and installing required packages..."

    # Update package list
    apt-get update -qq

    # Install hostapd and dnsmasq if not present
    PACKAGES_TO_INSTALL=""

    if ! dpkg -l | grep -q "^ii  hostapd "; then
        PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL hostapd"
    fi

    if ! dpkg -l | grep -q "^ii  dnsmasq "; then
        PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL dnsmasq"
    fi

    if ! dpkg -l | grep -q "^ii  iptables "; then
        PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL iptables"
    fi

    if [ -n "$PACKAGES_TO_INSTALL" ]; then
        log_message "Installing packages: $PACKAGES_TO_INSTALL"
        apt-get install -y $PACKAGES_TO_INSTALL
    else
        log_message "All required packages already installed"
    fi
}

# Stop conflicting services
stop_conflicting_services() {
    log_message "Stopping conflicting services..."

    # Stop system dnsmasq if running
    if systemctl is-active --quiet dnsmasq; then
        systemctl stop dnsmasq
        log_message "Stopped system dnsmasq service"
    fi

    # Stop system hostapd if running
    if systemctl is-active --quiet hostapd; then
        systemctl stop hostapd
        log_message "Stopped system hostapd service"
    fi

    # Stop NetworkManager from managing wlan0
    if systemctl is-active --quiet NetworkManager; then
        # Create NetworkManager configuration to ignore wlan0
        cat > /etc/NetworkManager/conf.d/99-unmanaged-devices.conf << EOF
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF
        systemctl reload NetworkManager
        log_message "Configured NetworkManager to ignore wlan0"
    fi
}

# Start WiFi hotspot using Python manager
start_hotspot() {
    log_message "Starting WiFi hotspot using Python manager..."

    cd "$WIFI_MANAGER_PATH"

    # Run the WiFi manager
    python3 wifi_manager.py start

    if [ $? -eq 0 ]; then
        log_message "WiFi hotspot started successfully"
        return 0
    else
        log_message "Failed to start WiFi hotspot"
        return 1
    fi
}

# Verify hotspot is working
verify_hotspot() {
    log_message "Verifying hotspot functionality..."

    # Check if wlan0 has the correct IP
    INTERFACE_IP=$(ip addr show wlan0 | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
    if [ "$INTERFACE_IP" != "192.168.12.1" ]; then
        log_message "WARNING: wlan0 IP is $INTERFACE_IP, expected 192.168.12.1"
    else
        log_message "✓ wlan0 configured with correct IP: $INTERFACE_IP"
    fi

    # Check if hostapd is running
    if pgrep -f hostapd > /dev/null; then
        log_message "✓ hostapd is running"
    else
        log_message "⚠ hostapd is not running"
    fi

    # Check if dnsmasq is running
    if pgrep -f dnsmasq > /dev/null; then
        log_message "✓ dnsmasq is running"
    else
        log_message "⚠ dnsmasq is not running"
    fi

    # Test if we can get hotspot status
    python3 "$WIFI_MANAGER_PATH/wifi_manager.py" status > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_message "✓ WiFi manager status check passed"
    else
        log_message "⚠ WiFi manager status check failed"
    fi
}

# Main execution
main() {
    log_message "Orange Pi WiFi Hotspot startup initiated"

    check_root
    install_dependencies
    stop_conflicting_services

    if start_hotspot; then
        sleep 3  # Give services time to start
        verify_hotspot
        log_message "WiFi hotspot startup completed successfully"
        exit 0
    else
        log_message "WiFi hotspot startup failed"
        exit 1
    fi
}

# Handle script arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "install-deps")
        check_root
        install_dependencies
        ;;
    "verify")
        verify_hotspot
        ;;
    *)
        echo "Usage: $0 {start|install-deps|verify}"
        echo "  start       - Start WiFi hotspot (default)"
        echo "  install-deps - Install required packages only"
        echo "  verify      - Verify hotspot status"
        exit 1
        ;;
esac
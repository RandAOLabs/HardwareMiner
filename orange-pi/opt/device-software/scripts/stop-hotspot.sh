#!/bin/bash
# Orange Pi WiFi Hotspot Stop Script
# Stop WiFi hotspot and clean up services

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

# Stop WiFi hotspot using Python manager
stop_hotspot() {
    log_message "Stopping WiFi hotspot using Python manager..."

    cd "$WIFI_MANAGER_PATH"

    # Run the WiFi manager stop command
    python3 wifi_manager.py stop

    if [ $? -eq 0 ]; then
        log_message "WiFi hotspot stopped successfully via Python manager"
    else
        log_message "Python manager stop failed, performing manual cleanup"
    fi
}

# Manual cleanup if needed
manual_cleanup() {
    log_message "Performing manual service cleanup..."

    # Kill hostapd processes
    if pgrep -f hostapd > /dev/null; then
        pkill -f hostapd
        log_message "Killed hostapd processes"
    fi

    # Kill dnsmasq processes
    if pgrep -f dnsmasq > /dev/null; then
        pkill -f dnsmasq
        log_message "Killed dnsmasq processes"
    fi

    # Remove PID files
    rm -f "$DEVICE_SOFTWARE_PATH/config/hostapd.pid"
    rm -f "$DEVICE_SOFTWARE_PATH/config/dnsmasq.pid"

    # Flush IP configuration from wlan0
    ip addr flush dev wlan0 2>/dev/null || true
    ip link set wlan0 down 2>/dev/null || true

    log_message "Manual cleanup completed"
}

# Restore normal WiFi functionality
restore_wifi() {
    log_message "Restoring normal WiFi functionality..."

    # Remove NetworkManager unmanaged configuration
    rm -f /etc/NetworkManager/conf.d/99-unmanaged-devices.conf

    # Reload NetworkManager if running
    if systemctl is-active --quiet NetworkManager; then
        systemctl reload NetworkManager
        log_message "NetworkManager reloaded"
    fi

    # Bring wlan0 back up for normal use
    ip link set wlan0 up 2>/dev/null || true

    log_message "Normal WiFi functionality restored"
}

# Verify hotspot is stopped
verify_stopped() {
    log_message "Verifying hotspot is stopped..."

    # Check for hostapd processes
    if pgrep -f hostapd > /dev/null; then
        log_message "⚠ hostapd processes still running"
        return 1
    else
        log_message "✓ No hostapd processes running"
    fi

    # Check for dnsmasq processes
    if pgrep -f dnsmasq > /dev/null; then
        log_message "⚠ dnsmasq processes still running"
        return 1
    else
        log_message "✓ No dnsmasq processes running"
    fi

    # Check if wlan0 still has hotspot IP
    INTERFACE_IP=$(ip addr show wlan0 2>/dev/null | grep "inet 192.168.12.1" || true)
    if [ -n "$INTERFACE_IP" ]; then
        log_message "⚠ wlan0 still has hotspot IP configuration"
        return 1
    else
        log_message "✓ wlan0 hotspot IP removed"
    fi

    log_message "Hotspot verification completed - all services stopped"
    return 0
}

# Main execution
main() {
    log_message "Orange Pi WiFi Hotspot shutdown initiated"

    check_root
    stop_hotspot
    manual_cleanup
    restore_wifi

    sleep 2  # Give services time to stop

    if verify_stopped; then
        log_message "WiFi hotspot shutdown completed successfully"
        exit 0
    else
        log_message "WiFi hotspot shutdown completed with warnings"
        exit 1
    fi
}

# Handle script arguments
case "${1:-stop}" in
    "stop")
        main
        ;;
    "cleanup")
        check_root
        manual_cleanup
        ;;
    "verify")
        verify_stopped
        ;;
    "restore")
        check_root
        restore_wifi
        ;;
    *)
        echo "Usage: $0 {stop|cleanup|verify|restore}"
        echo "  stop    - Stop WiFi hotspot (default)"
        echo "  cleanup - Manual cleanup of services"
        echo "  verify  - Verify hotspot is stopped"
        echo "  restore - Restore normal WiFi functionality"
        exit 1
        ;;
esac
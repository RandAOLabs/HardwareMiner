#!/bin/bash
#
# Direct Access Point Starter - Based on proven PI-setup implementation
# This script starts the WiFi hotspot using the exact same method that works
#

set -e

# Configuration matching proven working setup
INSTALL_DIR="/opt/rng-miner"
LOG_DIR="/var/log/rng-miner"
INTERFACE="wlan0"
AP_IP="192.168.4.1"
MAX_RETRIES=3
RETRY_DELAY=5

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | tee -a "$LOG_DIR/start_ap.log"
}

# Error handling
error_exit() {
    log "ERROR" "$1"
    cleanup_on_error
    exit 1
}

# Cleanup function
cleanup_on_error() {
    log "INFO" "Performing cleanup after error..."

    # Kill any running processes
    pkill -f hostapd 2>/dev/null || true
    pkill -f dnsmasq 2>/dev/null || true

    # Reset interface if possible
    if ip link show $INTERFACE >/dev/null 2>&1; then
        ip link set dev $INTERFACE down 2>/dev/null || true
        ip addr flush dev $INTERFACE 2>/dev/null || true

        # Re-enable NetworkManager management
        if command -v nmcli >/dev/null 2>&1; then
            nmcli device set $INTERFACE managed yes 2>/dev/null || true
        fi
    fi
}

# Wait for interface to be ready
wait_for_interface() {
    local interface="$1"
    local timeout=30
    local count=0

    log "INFO" "Waiting for interface $interface to be ready..."

    while [ $count -lt $timeout ]; do
        if ip link show $interface >/dev/null 2>&1; then
            log "INFO" "Interface $interface is available"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    log "ERROR" "Interface $interface not available after ${timeout}s"
    return 1
}

# Generate hostapd config using device ID
generate_hostapd_config() {
    local device_id_file="/var/lib/rng-miner/device_id"
    local device_id="UNKNOWN"

    if [[ -f "$device_id_file" ]]; then
        device_id=$(cat "$device_id_file" | head -1)
    fi

    local ssid="RNG-Miner-${device_id}"

    log "INFO" "Generating hostapd config for SSID: $ssid"

    cat > /etc/hostapd/hostapd.conf << EOF
# Ultra-minimal hostapd config to prevent crashes
interface=wlan0
driver=nl80211
ssid=$ssid
hw_mode=g
channel=6
auth_algs=1
wpa=0
country_code=US
wmm_enabled=0
ieee80211n=0
ignore_broadcast_ssid=0
macaddr_acl=0
logger_syslog=-1
logger_syslog_level=0
logger_stdout=-1
logger_stdout_level=0
ctrl_interface=/var/run/hostapd
EOF

    log "INFO" "Hostapd config generated for $ssid"
}

# Generate dnsmasq config
generate_dnsmasq_config() {
    log "INFO" "Generating dnsmasq configuration..."

    # Ensure dhcp directory exists
    mkdir -p /var/lib/dhcp
    touch /var/lib/dhcp/dnsmasq.leases
    chown root:root /var/lib/dhcp/dnsmasq.leases

    cat > /etc/dnsmasq.conf << EOF
# Simple dnsmasq configuration
interface=wlan0
bind-interfaces
except-interface=lo

# DHCP settings - match working PI-setup
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,12h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1

# DNS settings
no-resolv
server=8.8.8.8
server=8.8.4.4

# Captive portal - redirect all DNS queries
address=/#/192.168.4.1

# Basic settings
cache-size=150
dhcp-leasefile=/var/lib/dhcp/dnsmasq.leases
no-hosts
EOF

    log "INFO" "Dnsmasq configuration generated"
}

# Setup interface with retry logic
setup_interface() {
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        log "INFO" "Setting up interface (attempt $((retry_count + 1))/$MAX_RETRIES)..."

        # Stop conflicting services first
        log "INFO" "Stopping conflicting services..."
        systemctl stop hostapd 2>/dev/null || true
        systemctl stop dnsmasq 2>/dev/null || true
        systemctl stop wpa_supplicant 2>/dev/null || true

        # Kill any existing processes
        pkill -f hostapd 2>/dev/null || true
        pkill -f dnsmasq 2>/dev/null || true
        pkill -f "wpa_supplicant.*$INTERFACE" 2>/dev/null || true

        # Wait for processes to stop
        sleep 3

        # Bring down the interface
        if ip link set dev $INTERFACE down 2>/dev/null; then
            log "INFO" "Interface brought down successfully"
        else
            log "WARN" "Failed to bring down interface, continuing..."
        fi

        sleep 2

        # Remove any existing IP addresses
        ip addr flush dev $INTERFACE 2>/dev/null || true

        # Disable NetworkManager management temporarily
        if command -v nmcli >/dev/null 2>&1; then
            if nmcli device set $INTERFACE managed no 2>/dev/null; then
                log "INFO" "NetworkManager management disabled for $INTERFACE"
            else
                log "WARN" "Failed to disable NetworkManager management"
            fi
        fi

        sleep 1

        # Bring up the interface
        if ip link set dev $INTERFACE up; then
            log "INFO" "Interface brought up successfully"
        else
            log "ERROR" "Failed to bring up interface"
            retry_count=$((retry_count + 1))
            sleep $RETRY_DELAY
            continue
        fi

        sleep 2

        # Set static IP for the access point
        if ip addr add $AP_IP/24 dev $INTERFACE; then
            log "INFO" "IP address $AP_IP assigned successfully"
            return 0
        else
            log "ERROR" "Failed to assign IP address"
            retry_count=$((retry_count + 1))
            sleep $RETRY_DELAY
        fi
    done

    return 1
}

# Start hostapd with retry logic
start_hostapd() {
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        log "INFO" "Starting hostapd (attempt $((retry_count + 1))/$MAX_RETRIES)..."

        # Start hostapd in background
        if hostapd -B /etc/hostapd/hostapd.conf; then
            log "INFO" "Hostapd started successfully"

            # Wait and verify it's running
            sleep 5
            if pgrep hostapd >/dev/null; then
                log "INFO" "Hostapd is running and stable"
                return 0
            else
                log "ERROR" "Hostapd started but died immediately"
            fi
        else
            log "ERROR" "Failed to start hostapd"
        fi

        retry_count=$((retry_count + 1))
        sleep $RETRY_DELAY
    done

    return 1
}

# Start dnsmasq with retry logic
start_dnsmasq() {
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        log "INFO" "Starting dnsmasq (attempt $((retry_count + 1))/$MAX_RETRIES)..."

        # Stop systemd-resolved temporarily to free port 53
        log "INFO" "Temporarily stopping systemd-resolved to avoid port conflicts..."
        systemctl stop systemd-resolved 2>/dev/null || true

        # Kill any existing dnsmasq processes
        pkill -f dnsmasq 2>/dev/null || true
        sleep 2

        # Test configuration
        if dnsmasq --test --conf-file=/etc/dnsmasq.conf; then
            log "INFO" "Dnsmasq configuration is valid"
        else
            log "ERROR" "Dnsmasq configuration is invalid"
            retry_count=$((retry_count + 1))
            sleep $RETRY_DELAY
            continue
        fi

        # Start dnsmasq with specific interface binding
        if dnsmasq --interface=$INTERFACE --bind-interfaces --listen-address=$AP_IP --conf-file=/etc/dnsmasq.conf; then
            log "INFO" "Dnsmasq started successfully"

            # Wait and verify it's running
            sleep 3
            if pgrep dnsmasq >/dev/null; then
                log "INFO" "Dnsmasq is running and stable"
                return 0
            else
                log "ERROR" "Dnsmasq started but died immediately"
            fi
        else
            log "ERROR" "Failed to start dnsmasq"
        fi

        retry_count=$((retry_count + 1))
        sleep $RETRY_DELAY
    done

    return 1
}

# Main execution
main() {
    log "INFO" "=== Starting Direct Access Point Setup ==="
    log "INFO" "Interface: $INTERFACE"
    log "INFO" "AP IP: $AP_IP"

    # Check if we're running as root
    if [[ $EUID -ne 0 ]]; then
       error_exit "This script must be run as root"
    fi

    # Wait for interface to be available
    wait_for_interface "$INTERFACE" || error_exit "Interface $INTERFACE not available"

    # Generate configurations
    generate_hostapd_config
    generate_dnsmasq_config

    # Setup network interface
    setup_interface || error_exit "Failed to setup network interface after $MAX_RETRIES attempts"

    # Enable IP forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
    log "INFO" "IP forwarding enabled"

    # Start hostapd
    start_hostapd || error_exit "Failed to start hostapd after $MAX_RETRIES attempts"

    # Start dnsmasq
    start_dnsmasq || error_exit "Failed to start dnsmasq after $MAX_RETRIES attempts"

    # Final verification
    log "INFO" "Verifying services are running..."
    sleep 3

    if ! pgrep hostapd >/dev/null; then
        error_exit "Hostapd is not running after startup"
    fi

    if ! pgrep dnsmasq >/dev/null; then
        error_exit "Dnsmasq is not running after startup"
    fi

    # Check if interface has the correct IP
    if ! ip addr show $INTERFACE | grep -q "$AP_IP"; then
        error_exit "Interface does not have the correct IP address"
    fi

    log "INFO" "=== Access Point Setup Complete ==="
    local device_id=$(cat /var/lib/rng-miner/device_id 2>/dev/null || echo "UNKNOWN")
    log "INFO" "SSID: RNG-Miner-${device_id}"
    log "INFO" "Portal URL: http://$AP_IP:8080"
    log "INFO" "Interface: $INTERFACE ($AP_IP/24)"

    # Keep running to maintain the AP
    log "INFO" "Access point is running. Press Ctrl+C to stop."

    # Set up signal handling for graceful shutdown
    trap 'log "INFO" "Received shutdown signal, stopping services..."; cleanup_on_error; exit 0' SIGTERM SIGINT

    # Monitor services and restart if needed
    while true; do
        sleep 30

        # Check if hostapd is still running
        if ! pgrep hostapd >/dev/null; then
            log "WARN" "Hostapd died, restarting..."
            start_hostapd || log "ERROR" "Failed to restart hostapd"
        fi

        # Check if dnsmasq is still running
        if ! pgrep dnsmasq >/dev/null; then
            log "WARN" "Dnsmasq died, restarting..."
            start_dnsmasq || log "ERROR" "Failed to restart dnsmasq"
        fi
    done
}

# Run main function
main "$@"
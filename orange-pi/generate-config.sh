#!/bin/bash
#
# Generate RNG Miner device configuration
#

set -euo pipefail

INSTALL_DIR="/opt/rng-miner"
CONFIG_DIR="/etc/rng-miner"
DEVICE_ID_DIR="/var/lib/rng-miner"
DEVICE_ID_FILE="$DEVICE_ID_DIR/device_id"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🔧 Generating RNG Miner device configuration..."

# Create directories
mkdir -p "$CONFIG_DIR" "$DEVICE_ID_DIR"

# Generate device ID if it doesn't exist
if [[ ! -f "$DEVICE_ID_FILE" ]]; then
    log "🆔 Generating device ID..."

    # Try multiple methods to get a hardware identifier
    MAC_ADDR=""

    # Method 1: Get first MAC address from /sys
    if [[ -d /sys/class/net ]]; then
        for iface in /sys/class/net/*/address; do
            if [[ -f "$iface" ]]; then
                addr=$(cat "$iface" 2>/dev/null || echo "")
                if [[ "$addr" != "00:00:00:00:00:00" ]] && [[ -n "$addr" ]]; then
                    MAC_ADDR=$(echo "$addr" | tr -d ':')
                    break
                fi
            fi
        done
    fi

    # Method 2: Use ip command as backup
    if [[ -z "$MAC_ADDR" ]]; then
        MAC_ADDR=$(ip link show 2>/dev/null | awk '/link\/ether/ && !/00:00:00:00:00:00/ {print $2; exit}' | tr -d ':' || echo "")
    fi

    # Method 3: Fallback to random
    if [[ -z "$MAC_ADDR" ]]; then
        MAC_ADDR="$(openssl rand -hex 6)"
        log "No valid MAC found, using random: $MAC_ADDR"
    fi

    # Get hostname
    HOSTNAME=$(hostname 2>/dev/null || echo "orangepi")

    # Generate device ID
    TIMESTAMP=$(date +%s)
    DEVICE_ID=$(echo -n "${MAC_ADDR}${HOSTNAME}${TIMESTAMP}" | sha256sum | cut -c1-8 | tr 'a-z' 'A-Z')

    # Save device ID
    echo "$DEVICE_ID" > "$DEVICE_ID_FILE"

    log "✅ Device ID generated: $DEVICE_ID"

    # Set hostname to match AP name (RNG-Miner-XXXXXXXX)
    NEW_HOSTNAME="RNG-Miner-${DEVICE_ID}"
    log "🏷️  Setting hostname to: $NEW_HOSTNAME"

    # Update hostname in multiple places
    echo "$NEW_HOSTNAME" > /etc/hostname
    hostnamectl set-hostname "$NEW_HOSTNAME" 2>/dev/null || true

    # Update /etc/hosts to include new hostname
    sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/g" /etc/hosts
    # Add if not exists
    grep -q "127.0.1.1" /etc/hosts || echo "127.0.1.1	$NEW_HOSTNAME" >> /etc/hosts

    log "✅ Hostname set to $NEW_HOSTNAME"
else
    DEVICE_ID=$(cat "$DEVICE_ID_FILE")
    log "✅ Device ID exists: $DEVICE_ID"
fi

# Set proper permissions
chown -R orangepi:orangepi "$DEVICE_ID_DIR" 2>/dev/null || chown -R pi:pi "$DEVICE_ID_DIR" 2>/dev/null || chown -R root:root "$DEVICE_ID_DIR"

# Generate SSL certificate if it doesn't exist
if [[ ! -f "$CONFIG_DIR/server.crt" ]] || [[ ! -f "$CONFIG_DIR/server.key" ]]; then
    log "🔒 Generating SSL certificate..."

    openssl req -x509 -newkey rsa:2048 -keyout "$CONFIG_DIR/server.key" -out "$CONFIG_DIR/server.crt" \
        -days 365 -nodes -subj "/C=US/ST=CA/L=SF/O=RNG-Miner/CN=rng-miner-${DEVICE_ID}" 2>/dev/null

    chmod 600 "$CONFIG_DIR/server.key"
    chmod 644 "$CONFIG_DIR/server.crt"

    log "✅ SSL certificate generated"
else
    log "✅ SSL certificate exists"
fi

# Install missing Python packages if needed
if ! python3 -c "import netifaces" 2>/dev/null; then
    log "Installing netifaces..."
    pip3 install netifaces
fi

log "🎉 Device configuration complete!"
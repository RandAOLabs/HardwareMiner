#!/bin/bash
#
# RNG Miner Orange Pi Installation Script
#
# This script sets up everything needed for the RNG Miner device:
# - HTTP server with HTTPS
# - WiFi hotspot capability
# - Mining software preparation
# - Auto-start services
#
# Usage: sudo ./install.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

log "🍊 Starting RNG Miner Orange Pi Installation..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/rng-miner"

log "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Set non-interactive mode for all package operations
export DEBIAN_FRONTEND=noninteractive

# Pre-configure packages to avoid prompts
log "🔧 Pre-configuring packages..."
echo 'openssh-server openssh-server/permit-root-login select false' | debconf-set-selections
echo 'dnsmasq dnsmasq/confdir string /etc/dnsmasq.d' | debconf-set-selections
echo 'hostapd hostapd/daemon_conf string /etc/hostapd/hostapd.conf' | debconf-set-selections

# Update system
log "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required packages with no prompts
log "⚙️  Installing required packages..."
apt install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-flask \
    python3-flask-cors \
    python3-cryptography \
    python3-requests \
    python3-psutil \
    python3-netifaces \
    curl \
    wget \
    git \
    network-manager \
    openssl

# Install WiFi packages separately with explicit configuration
log "📡 Installing WiFi hotspot packages..."
DEBIAN_FRONTEND=noninteractive apt install -y hostapd dnsmasq

# Create dnsmasq user/group if missing
log "👤 Ensuring dnsmasq user exists..."
if ! id dnsmasq >/dev/null 2>&1; then
    useradd -r -s /bin/false -d /var/lib/dnsmasq -c "dnsmasq daemon" dnsmasq 2>/dev/null || true
fi

# Ensure hostapd is properly configured
log "🔧 Configuring hostapd..."
systemctl unmask hostapd 2>/dev/null || true
systemctl disable hostapd 2>/dev/null || true
systemctl stop hostapd 2>/dev/null || true

# Ensure dnsmasq is properly configured
log "🔧 Configuring dnsmasq..."
systemctl disable dnsmasq 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# Install Docker for mining software (non-interactive)
log "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    DEBIAN_FRONTEND=noninteractive sh get-docker.sh
    usermod -aG docker orangepi 2>/dev/null || usermod -aG docker pi 2>/dev/null || true
    rm get-docker.sh
else
    log "Docker already installed"
fi

# Install Docker Compose via system package manager
log "📋 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    # Try to install docker-compose-plugin (modern approach)
    apt install -y docker-compose-plugin 2>/dev/null || {
        # Fallback: install standalone docker-compose
        apt install -y docker-compose 2>/dev/null || {
            log "Warning: Could not install docker-compose via apt, will use docker compose plugin"
        }
    }
else
    log "Docker Compose already available"
fi

# Copy all files to installation directory
log "📋 Copying RNG Miner files..."
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"

# Set up Python virtual environment (quiet)
log "🐍 Setting up Python environment..."
cd "$INSTALL_DIR"
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Only install packages that aren't available system-wide
log "🐍 Installing additional Python packages..."
pip install --quiet --no-warn-script-location -r requirements.txt 2>/dev/null || {
    log "Note: Using system Python packages where available"
}

# Create necessary directories
log "📁 Creating directory structure..."
mkdir -p /var/log/rng-miner
mkdir -p /etc/rng-miner
mkdir -p /var/lib/rng-miner

# Set permissions
log "🔒 Setting permissions..."
chown -R orangepi:orangepi "$INSTALL_DIR" 2>/dev/null || chown -R pi:pi "$INSTALL_DIR" 2>/dev/null || true
chown -R orangepi:orangepi /var/log/rng-miner 2>/dev/null || chown -R pi:pi /var/log/rng-miner 2>/dev/null || true
chown -R orangepi:orangepi /var/lib/rng-miner 2>/dev/null || chown -R pi:pi /var/lib/rng-miner 2>/dev/null || true

# Make scripts executable
chmod +x "$INSTALL_DIR"/*.sh
chmod +x "$INSTALL_DIR"/scripts/*.sh 2>/dev/null || true

# Install systemd service
log "⚡ Installing systemd service..."
cat > /etc/systemd/system/rng-miner.service << EOF
[Unit]
Description=RNG Miner HTTP Server and WiFi Hotspot
After=network.target
Wants=network.target

[Service]
Type=forking
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh
ExecStop=$INSTALL_DIR/stop.sh
ExecReload=$INSTALL_DIR/restart.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Generate device configuration
log "🔧 Generating device configuration..."
if [[ -f "$INSTALL_DIR/generate-config.sh" ]]; then
    "$INSTALL_DIR/generate-config.sh"
else
    # Generate device ID directly if script missing
    log "🆔 Generating device ID..."
    DEVICE_ID_DIR="/var/lib/rng-miner"
    mkdir -p "$DEVICE_ID_DIR"

    # Get MAC address for device ID
    MAC_ADDR=$(ip link show | awk '/link\/ether/ {print $2; exit}' | tr -d ':' | head -c12)
    if [[ -z "$MAC_ADDR" ]]; then
        MAC_ADDR="000000000000"
    fi

    HOSTNAME=$(hostname 2>/dev/null || echo "orangepi")
    DEVICE_ID=$(echo -n "${MAC_ADDR}${HOSTNAME}$(date +%s)" | sha256sum | cut -c1-8 | tr 'a-z' 'A-Z')
    echo "$DEVICE_ID" > "$DEVICE_ID_DIR/device_id"

    # Set proper permissions
    chown -R orangepi:orangepi "$DEVICE_ID_DIR" 2>/dev/null || chown -R pi:pi "$DEVICE_ID_DIR" 2>/dev/null || true

    log "Device ID: $DEVICE_ID"
fi

# Enable the service
log "🚀 Enabling RNG Miner service..."
systemctl daemon-reload
systemctl enable rng-miner.service

# Fix systemd-resolved port 53 conflict
log "🔧 Fixing DNS port conflicts..."
# Disable systemd-resolved DNS stub to free port 53
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/disable-stub.conf << EOF
[Resolve]
DNS=8.8.8.8 1.1.1.1
DNSStubListener=no
EOF

# Stop and disable systemd-resolved temporarily
systemctl stop systemd-resolved
systemctl disable systemd-resolved

# Create manual resolv.conf and disable resolvconf integration
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# NUCLEAR: Completely eliminate resolvconf to avoid dnsmasq conflicts
log "🔥 NUCLEAR: Completely eliminating resolvconf..."

# Kill all running resolvconf processes
pkill resolvconf 2>/dev/null || true
sleep 2

# Stop and mask all related services
systemctl stop resolvconf 2>/dev/null || true
systemctl disable resolvconf 2>/dev/null || true
systemctl mask resolvconf 2>/dev/null || true

# Remove the binaries to prevent execution
if [[ -f /sbin/resolvconf ]]; then
    mv /sbin/resolvconf /sbin/resolvconf.disabled 2>/dev/null || true
fi

if [[ -f /usr/sbin/resolvconf ]]; then
    mv /usr/sbin/resolvconf /usr/sbin/resolvconf.disabled 2>/dev/null || true
fi

# Remove ALL resolvconf directories and configs
rm -rf /etc/resolvconf/ 2>/dev/null || true
rm -rf /run/resolvconf/ 2>/dev/null || true
rm -rf /var/lib/resolvconf/ 2>/dev/null || true

# Remove packages completely (including openresolv)
DEBIAN_FRONTEND=noninteractive apt remove --purge -y resolvconf openresolv 2>/dev/null || true

# Create a fake resolvconf that does nothing
cat > /sbin/resolvconf << 'EOF'
#!/bin/bash
# Fake resolvconf - does nothing to prevent interference
exit 0
EOF

chmod +x /sbin/resolvconf

# Also create fake in /usr/sbin if needed
cp /sbin/resolvconf /usr/sbin/resolvconf 2>/dev/null || true

# Protect our manual resolv.conf from any changes
chattr -i /etc/resolv.conf 2>/dev/null || true
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
chattr +i /etc/resolv.conf 2>/dev/null || true

log "✅ resolvconf completely eliminated and resolv.conf protected"

# Configure NetworkManager to allow hotspot switching
log "🌐 Configuring NetworkManager for flexible wlan0 management..."
mkdir -p /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/99-rng-miner.conf << EOF
# Allow NetworkManager to manage wlan0 but don't auto-connect
[main]
no-auto-default=wlan0

[device-wlan0]
match-device=interface-name:wlan0
managed=true
EOF

# Restart NetworkManager to apply the configuration
systemctl restart NetworkManager 2>/dev/null || true
sleep 2

# Bring wlan0 up for initial detection
ip link set wlan0 up 2>/dev/null || true

# Override dnsmasq systemd service to disable D-Bus completely
log "🔧 Configuring dnsmasq service to avoid D-Bus..."
mkdir -p /etc/systemd/system/dnsmasq.service.d
cat > /etc/systemd/system/dnsmasq.service.d/99-no-dbus.conf << EOF
[Service]
# COMPLETELY override dnsmasq service to disable ALL integrations
ExecStart=
ExecStart=/usr/sbin/dnsmasq --conf-file=/etc/dnsmasq.conf --keep-in-foreground --no-daemon --no-poll
ExecStartPre=
ExecStartPost=
ExecReload=
Type=simple
PIDFile=
Restart=always
RestartSec=5
# Disable ALL external integrations
Environment="DBUS_SESSION_BUS_ADDRESS="
Environment="DBUS_SYSTEM_BUS_ADDRESS="
Environment="RESOLVCONF=NO"
Environment="SYSTEMD_IGNORE_CHROOT=1"
# Run as root and isolate completely
User=root
Group=root
PrivateNetwork=false
NoNewPrivileges=false
# Kill any D-Bus attempts
KillMode=mixed
TimeoutStopSec=10
EOF

# Also create a wrapper script to completely isolate dnsmasq
cat > /usr/local/bin/dnsmasq-isolated << 'SCRIPT_EOF'
#!/bin/bash
# Isolated dnsmasq launcher - no D-Bus, no systemd integration

# Unset all D-Bus environment variables
unset DBUS_SESSION_BUS_ADDRESS
unset DBUS_SYSTEM_BUS_ADDRESS
unset SYSTEMD_IGNORE_CHROOT

# Kill any existing dnsmasq processes
pkill dnsmasq 2>/dev/null || true
sleep 1

# Run dnsmasq in completely isolated mode
exec /usr/sbin/dnsmasq \
    --conf-file=/etc/dnsmasq.conf \
    --keep-in-foreground \
    --no-daemon \
    --no-poll \
    --no-resolv \
    --bind-interfaces \
    --except-interface=lo \
    --log-facility=/var/log/dnsmasq-isolated.log \
    --log-queries \
    --log-dhcp
SCRIPT_EOF

chmod +x /usr/local/bin/dnsmasq-isolated

# Update the service to use our isolated wrapper
cat > /etc/systemd/system/dnsmasq.service.d/99-no-dbus.conf << EOF
[Service]
# Use completely isolated dnsmasq wrapper
ExecStart=
ExecStart=/usr/local/bin/dnsmasq-isolated
ExecStartPre=
ExecStartPost=
ExecReload=
Type=simple
PIDFile=
Restart=always
RestartSec=5
User=root
Group=root
Environment="DBUS_SESSION_BUS_ADDRESS="
Environment="DBUS_SYSTEM_BUS_ADDRESS="
KillMode=mixed
TimeoutStopSec=10
EOF

# Reload systemd to apply the override
systemctl daemon-reload

log "✅ Installation complete!"
log ""
log "📋 Next steps:"
log "1. Reboot the Orange Pi: sudo reboot"
log "2. After reboot, the device will:"
log "   - Start HTTP server on port 8080"
log "   - Create WiFi hotspot: RNG-Miner-XXXXXXXX"
log "   - Password: RNG-Miner-Password-123"
log "3. Connect with mobile app to configure"
log ""
log "🔧 Service management:"
log "   sudo systemctl start rng-miner    # Start service"
log "   sudo systemctl stop rng-miner     # Stop service"
log "   sudo systemctl status rng-miner   # Check status"
log "   sudo journalctl -u rng-miner -f   # View logs"
log ""
warn "⚠️  Disconnect ethernet/WiFi before rebooting to ensure hotspot mode"
#!/bin/bash
# Super Simple Orange Pi Startup Script
# Just starts WiFi hotspot and HTTP server - nothing fancy

set -e

LOG_FILE="/opt/device-software/logs/simple-startup.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p "/opt/device-software/logs"

log "🚀 Simple RNG-Miner startup starting..."

# Kill any existing processes
log "🔴 Stopping existing processes..."
pkill -f "app.py" 2>/dev/null || true
pkill -f "server.py" 2>/dev/null || true
pkill -f "hostapd" 2>/dev/null || true
pkill -f "dnsmasq" 2>/dev/null || true

# Wait for processes to stop
sleep 3

# Set up network interface
log "📡 Setting up network interface..."
ip link set wlan0 down 2>/dev/null || true
sleep 2
ip addr flush dev wlan0 2>/dev/null || true
ip addr add 192.168.4.1/24 dev wlan0 2>/dev/null || true
ip link set wlan0 up 2>/dev/null || true

# Check if interface is up
if ip addr show wlan0 | grep "192.168.4.1" > /dev/null; then
    log "✅ Network interface configured: 192.168.4.1"
else
    log "⚠️ Network interface may not be configured correctly"
fi

# Create simple hostapd config
log "📝 Creating hostapd configuration..."
cat > /tmp/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=RNG-Miner-Simple
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=RNG-Miner-Password-123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Start hostapd
log "🛜 Starting hostapd..."
hostapd -B /tmp/hostapd.conf 2>&1 | tee -a "$LOG_FILE"

# Wait for hostapd to start
sleep 3

# Create simple dnsmasq config
log "📝 Creating dnsmasq configuration..."
cat > /tmp/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=192.168.4.100,192.168.4.200,255.255.255.0,24h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
EOF

# Start dnsmasq
log "🌐 Starting dnsmasq..."
dnsmasq --conf-file=/tmp/dnsmasq.conf --no-daemon &

# Wait for dnsmasq to start
sleep 2

# Configure firewall
log "🧱 Configuring firewall..."
iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
iptables -I INPUT -s 192.168.4.0/24 -j ACCEPT 2>/dev/null || true

# Start HTTP server
log "🚀 Starting HTTP server..."
cd /opt/device-software/src/simple-server

# Install flask if needed
pip3 install flask 2>/dev/null || true

# Start the server
python3 app.py 2>&1 | tee -a "$LOG_FILE" &
SERVER_PID=$!

# Wait and check if server started
sleep 5

if ps -p $SERVER_PID > /dev/null; then
    log "✅ HTTP server started successfully (PID: $SERVER_PID)"
else
    log "❌ HTTP server failed to start"
    exit 1
fi

# Test server
log "🔍 Testing server..."
if curl -s http://192.168.4.1/health > /dev/null 2>&1; then
    log "✅ Server is responding to health checks"
    curl -s http://192.168.4.1/health | log "Response: $(cat)"
else
    log "⚠️ Server health check failed"
fi

log "🎉 Simple startup complete!"
log "📱 Connect to WiFi: RNG-Miner-Simple"
log "🔗 Password: RNG-Miner-Password-123"
log "🌐 Test URL: http://192.168.4.1/health"

# Keep script running
wait
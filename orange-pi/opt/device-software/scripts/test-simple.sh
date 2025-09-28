#!/bin/bash
# Test script for the simple HTTP server

echo "🧪 Testing Simple RNG-Miner HTTP Server"
echo "========================================"

# Test localhost
echo ""
echo "🔍 Testing localhost..."
if curl -s -m 5 http://localhost/health > /dev/null 2>&1; then
    echo "✅ localhost/health - OK"
    curl -s http://localhost/health | jq . 2>/dev/null || curl -s http://localhost/health
else
    echo "❌ localhost/health - FAILED"
fi

# Test 192.168.4.1
echo ""
echo "🔍 Testing 192.168.4.1..."
if curl -s -m 5 http://192.168.4.1/health > /dev/null 2>&1; then
    echo "✅ 192.168.4.1/health - OK"
    curl -s http://192.168.4.1/health | jq . 2>/dev/null || curl -s http://192.168.4.1/health
else
    echo "❌ 192.168.4.1/health - FAILED"
fi

# Test device info
echo ""
echo "🔍 Testing device info..."
if curl -s -m 5 http://192.168.4.1/device/info > /dev/null 2>&1; then
    echo "✅ /device/info - OK"
    echo "Response preview:"
    curl -s http://192.168.4.1/device/info | jq '.device_id, .model, .wifi_state' 2>/dev/null || echo "Could not format JSON"
else
    echo "❌ /device/info - FAILED"
fi

# Test network interface
echo ""
echo "🔍 Network interface status:"
ip addr show wlan0 | grep "192.168.4.1" && echo "✅ Interface has correct IP" || echo "❌ Interface IP missing"

# Test processes
echo ""
echo "🔍 Process status:"
pgrep -f "app.py" >/dev/null && echo "✅ Python server running" || echo "❌ Python server not found"
pgrep -f "hostapd" >/dev/null && echo "✅ hostapd running" || echo "❌ hostapd not found"
pgrep -f "dnsmasq" >/dev/null && echo "✅ dnsmasq running" || echo "❌ dnsmasq not found"

# Test port
echo ""
echo "🔍 Port status:"
netstat -tln | grep ":80 " >/dev/null && echo "✅ Port 80 listening" || echo "❌ Port 80 not listening"

echo ""
echo "🎯 For mobile testing:"
echo "   Connect to WiFi: RNG-Miner-Simple"
echo "   Password: RNG-Miner-Password-123"
echo "   Test URL: http://192.168.4.1/health"
echo ""
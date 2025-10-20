#!/bin/bash
#
# Nuclear option: Completely eliminate resolvconf
#

set -euo pipefail

echo "🔥 NUCLEAR: Completely eliminating resolvconf..."

# Kill all running resolvconf processes
pkill resolvconf 2>/dev/null || true
sleep 2

# Stop and mask all related services
systemctl stop resolvconf 2>/dev/null || true
systemctl disable resolvconf 2>/dev/null || true
systemctl mask resolvconf 2>/dev/null || true

# Remove the binary to prevent execution
if [[ -f /sbin/resolvconf ]]; then
    mv /sbin/resolvconf /sbin/resolvconf.disabled 2>/dev/null || true
fi

if [[ -f /usr/sbin/resolvconf ]]; then
    mv /usr/sbin/resolvconf /usr/sbin/resolvconf.disabled 2>/dev/null || true
fi

# Remove all resolvconf directories and configs
rm -rf /etc/resolvconf/ 2>/dev/null || true
rm -rf /run/resolvconf/ 2>/dev/null || true
rm -rf /var/lib/resolvconf/ 2>/dev/null || true

# Remove package completely
DEBIAN_FRONTEND=noninteractive apt remove --purge -y resolvconf openresolv 2>/dev/null || true

# Create a fake resolvconf that does nothing
cat > /sbin/resolvconf << 'EOF'
#!/bin/bash
# Fake resolvconf - does nothing
exit 0
EOF

chmod +x /sbin/resolvconf

# Protect resolv.conf
chattr -i /etc/resolv.conf 2>/dev/null || true
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
chattr +i /etc/resolv.conf 2>/dev/null || true

echo "✅ resolvconf completely eliminated!"
echo "🔄 Run 'sudo systemctl restart dnsmasq' to test"
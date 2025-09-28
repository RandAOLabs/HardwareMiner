#!/usr/bin/env python3
"""
WiFi Manager for RNG Miner

Handles WiFi hotspot creation and client WiFi connections.
"""

import os
import time
import logging
import subprocess
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class WiFiManager:
    def __init__(self):
        self.device_id_file = Path("/var/lib/rng-miner/device_id")
        self.hotspot_active = False

    def get_device_id(self):
        """Get the device ID for hotspot SSID."""
        if self.device_id_file.exists():
            with open(self.device_id_file, 'r') as f:
                return f.read().strip()
        return "UNKNOWN"

    def run_command(self, command, check=True):
        """Run a shell command and return result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {e.stderr}")
            raise

    def generate_hostapd_config(self):
        """Generate hostapd configuration file using proven working config."""
        device_id = self.get_device_id()
        ssid = f"RNG-Miner-{device_id}"

        config = f"""# Ultra-minimal hostapd config to prevent crashes with unisoc_wifi
interface=wlan0
driver=nl80211
ssid={ssid}
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
"""

        hostapd_conf = Path("/etc/hostapd/hostapd.conf")
        with open(hostapd_conf, 'w') as f:
            f.write(config)

        logger.info(f"Generated hostapd config for SSID: {ssid}")
        return ssid

    def generate_dnsmasq_config(self):
        """Generate dnsmasq configuration using proven working setup."""
        # Ensure dhcp directory exists
        dhcp_dir = Path("/var/lib/dhcp")
        dhcp_dir.mkdir(exist_ok=True)
        leases_file = dhcp_dir / "dnsmasq.leases"
        leases_file.touch()

        config = """# Simple dnsmasq configuration
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
"""

        dnsmasq_conf = Path("/etc/dnsmasq.conf")

        # Backup original config
        if dnsmasq_conf.exists() and not Path("/etc/dnsmasq.conf.backup").exists():
            self.run_command(f"cp {dnsmasq_conf} /etc/dnsmasq.conf.backup")

        with open(dnsmasq_conf, 'w') as f:
            f.write(config)

        logger.info("Generated dnsmasq config")

    def setup_interface(self):
        """Set up wlan0 interface for hotspot using proven method."""
        try:
            logger.info("Setting up wlan0 interface for hotspot...")

            # Stop conflicting services (like working version)
            self.run_command("systemctl stop hostapd", check=False)
            self.run_command("systemctl stop dnsmasq", check=False)
            self.run_command("systemctl stop wpa_supplicant", check=False)

            # Kill any existing processes
            self.run_command("pkill -f hostapd", check=False)
            self.run_command("pkill -f dnsmasq", check=False)
            self.run_command("pkill -f wpa_supplicant.*wlan0", check=False)

            # Wait for processes to stop
            time.sleep(3)

            # Bring interface down
            self.run_command("ip link set dev wlan0 down", check=False)
            time.sleep(2)

            # Flush any existing addresses
            self.run_command("ip addr flush dev wlan0", check=False)

            # Disable NetworkManager management
            self.run_command("nmcli device set wlan0 managed no", check=False)
            time.sleep(1)

            # Bring interface up
            self.run_command("ip link set dev wlan0 up")
            time.sleep(2)

            # Set static IP (matching proven working version)
            self.run_command("ip addr add 192.168.4.1/24 dev wlan0")
            time.sleep(2)

            # Verify interface and IP
            result = self.run_command("ip addr show wlan0")
            if "192.168.4.1" not in result:
                raise Exception("Failed to assign IP address to wlan0")

            logger.info("Interface wlan0 configured successfully: 192.168.4.1/24")

        except Exception as e:
            logger.error(f"Failed to setup interface: {e}")
            raise

    def start_hotspot(self):
        """Start WiFi hotspot using direct method (no systemd)."""
        try:
            if self.hotspot_active:
                logger.info("Hotspot already active")
                return

            logger.info("Starting WiFi hotspot...")

            # Generate configurations
            ssid = self.generate_hostapd_config()
            self.generate_dnsmasq_config()

            # Setup network interface
            self.setup_interface()

            # Enable IP forwarding
            self.run_command("echo 1 > /proc/sys/net/ipv4/ip_forward")

            # Stop systemd-resolved to free port 53 (CRITICAL)
            logger.info("Stopping systemd-resolved to free port 53...")
            self.run_command("systemctl stop systemd-resolved", check=False)
            time.sleep(2)

            # Kill any existing dnsmasq processes
            self.run_command("pkill -f dnsmasq", check=False)
            time.sleep(2)

            # Test dnsmasq configuration before starting
            logger.info("Testing dnsmasq configuration...")
            try:
                self.run_command("dnsmasq --test --conf-file=/etc/dnsmasq.conf")
                logger.info("Dnsmasq configuration is valid")
            except:
                logger.warning("Dnsmasq config test failed, proceeding anyway...")

            # Start dnsmasq directly with specific binding (bypass systemd)
            logger.info("Starting dnsmasq directly with interface binding...")
            self.run_command("dnsmasq --interface=wlan0 --bind-interfaces --listen-address=192.168.4.1 --conf-file=/etc/dnsmasq.conf &")
            time.sleep(3)

            # Verify dnsmasq is running
            try:
                self.run_command("pgrep dnsmasq")
                logger.info("Dnsmasq is running")
            except:
                raise Exception("Dnsmasq failed to start")

            # Kill any existing hostapd processes
            self.run_command("pkill -f hostapd", check=False)
            time.sleep(2)

            # Start hostapd directly (bypass systemd)
            logger.info("Starting hostapd directly...")
            self.run_command("hostapd -B /etc/hostapd/hostapd.conf")
            time.sleep(3)

            # Verify hostapd is running
            try:
                self.run_command("pgrep hostapd")
                logger.info("Hostapd is running")
            except:
                raise Exception("Hostapd failed to start")

            # Final verification
            self.run_command("ip addr show wlan0")

            self.hotspot_active = True
            logger.info(f"✅ WiFi hotspot started successfully: {ssid}")
            logger.info("AP Available at: http://192.168.4.1")

        except Exception as e:
            logger.error(f"Failed to start hotspot: {e}")
            self.stop_hotspot()  # Cleanup on failure
            raise

    def stop_hotspot(self):
        """Stop WiFi hotspot."""
        try:
            logger.info("Stopping WiFi hotspot...")

            # Stop services
            self.run_command("systemctl stop hostapd", check=False)
            self.run_command("systemctl stop dnsmasq", check=False)

            # Restore NetworkManager control
            self.run_command("nmcli device set wlan0 managed yes", check=False)

            # Flush interface
            self.run_command("ip addr flush dev wlan0", check=False)

            self.hotspot_active = False
            logger.info("WiFi hotspot stopped")

        except Exception as e:
            logger.error(f"Error stopping hotspot: {e}")

    def get_hotspot_status(self):
        """Get current hotspot status."""
        try:
            # Check if hostapd is running
            try:
                self.run_command("systemctl is-active hostapd")
                hostapd_active = True
            except:
                hostapd_active = False

            # Check if dnsmasq is running
            try:
                self.run_command("systemctl is-active dnsmasq")
                dnsmasq_active = True
            except:
                dnsmasq_active = False

            # Count connected clients
            connected_clients = 0
            try:
                # Check DHCP leases - use correct location
                leases_file = Path("/var/lib/dhcp/dnsmasq.leases")
                if leases_file.exists():
                    with open(leases_file, 'r') as f:
                        content = f.read()
                        # Count active leases more accurately
                        connected_clients = len([line for line in content.split('\n') if line.strip() and not line.startswith('#')])
                else:
                    connected_clients = 0
            except:
                pass

            device_id = self.get_device_id()
            ssid = f"RNG-Miner-{device_id}"

            return {
                "active": hostapd_active and dnsmasq_active,
                "ssid": ssid if hostapd_active else None,
                "clients": connected_clients,
                "services": {
                    "hostapd": hostapd_active,
                    "dnsmasq": dnsmasq_active
                }
            }

        except Exception as e:
            logger.error(f"Error getting hotspot status: {e}")
            return {
                "active": False,
                "ssid": None,
                "clients": 0,
                "error": str(e)
            }

    def connect_to_wifi(self, ssid, password):
        """Connect to WiFi network."""
        try:
            logger.info(f"Connecting to WiFi: {ssid}")

            # Stop hotspot first
            self.stop_hotspot()

            # Create NetworkManager connection
            cmd = f'nmcli device wifi connect "{ssid}" password "{password}"'
            self.run_command(cmd)

            # Wait for connection
            time.sleep(10)

            # Verify connection
            result = self.run_command("nmcli -t -f WIFI g")
            if "enabled" in result:
                logger.info(f"✅ Connected to WiFi: {ssid}")
            else:
                raise Exception("WiFi connection failed")

        except Exception as e:
            logger.error(f"Failed to connect to WiFi: {e}")
            # Restart hotspot on failure
            self.start_hotspot()
            raise

    def get_status(self):
        """Get current WiFi status."""
        try:
            # Check if connected to WiFi
            try:
                result = self.run_command("nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes'")
                if result:
                    connected_ssid = result.split(':')[1]
                    return {
                        "state": "CONNECTED",
                        "ssid": connected_ssid,
                        "mode": "client"
                    }
            except:
                pass

            # Check hotspot status
            hotspot_status = self.get_hotspot_status()
            if hotspot_status["active"]:
                return {
                    "state": "HOTSPOT",
                    "ssid": hotspot_status["ssid"],
                    "mode": "hotspot",
                    "clients": hotspot_status["clients"]
                }

            return {
                "state": "DISCONNECTED",
                "mode": "unknown"
            }

        except Exception as e:
            logger.error(f"Error getting WiFi status: {e}")
            return {
                "state": "ERROR",
                "error": str(e)
            }
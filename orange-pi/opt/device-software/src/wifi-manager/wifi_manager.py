#!/usr/bin/env python3
"""
Orange Pi WiFi Manager
Handles WiFi hotspot creation, DHCP configuration, and network interface management
"""

import os
import sys
import json
import time
import signal
import logging
import hashlib
import subprocess
import socket
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

class WiFiManager:
    """Manages WiFi hotspot creation and lifecycle on Orange Pi"""

    def __init__(self, config_path="/opt/device-software/config/device-config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.device_id = self.get_or_generate_device_id()
        self.hotspot_active = False
        self.setup_logging()

        # File paths
        self.hostapd_config_path = "/opt/device-software/config/hostapd.conf"
        self.dnsmasq_config_path = "/opt/device-software/config/dnsmasq.conf"
        self.hostapd_pid_file = "/opt/device-software/config/hostapd.pid"
        self.dnsmasq_pid_file = "/opt/device-software/config/dnsmasq.pid"

        # Network configuration
        self.hotspot_interface = "wlan0"
        self.hotspot_ip = "192.168.4.1"
        self.hotspot_subnet = "192.168.4.0/24"
        self.dhcp_range_start = "192.168.4.100"
        self.dhcp_range_end = "192.168.4.200"
        self.hotspot_password = "RNG-Miner-Password-123"

    def load_config(self) -> Dict:
        """Load device configuration from JSON file"""
        default_config = {
            "device_id": "",
            "hotspot_ssid": "",
            "hotspot_password": "RNG-Miner-Password-123",
            "http_port": 8080,
            "dhcp_range": "192.168.4.0/24",
            "wifi_state_timeout": 30,
            "connection_retry_limit": 3
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            return default_config
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return default_config

    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self.config["device_id"] = self.device_id
            self.config["hotspot_ssid"] = f"RNG-Miner-{self.device_id}"
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def get_or_generate_device_id(self) -> str:
        """Get existing device ID or generate new one"""
        # Check if device ID already exists in config
        if self.config.get("device_id"):
            return self.config["device_id"]

        # Generate new device ID
        device_id = self.generate_device_id()
        logging.info(f"Generated new device ID: {device_id}")
        return device_id

    def generate_device_id(self) -> str:
        """Generate 8-character unique device ID based on hardware identifiers"""
        try:
            identifiers = []

            # MAC address of wlan0 interface
            try:
                mac_address = self.get_interface_mac('wlan0')
                identifiers.append(mac_address)
            except:
                pass

            # CPU serial number
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('Serial'):
                            serial = line.split(':')[1].strip()
                            if serial and serial != "0000000000000000":
                                identifiers.append(serial)
                            break
            except:
                pass

            # Machine ID
            try:
                with open('/etc/machine-id', 'r') as f:
                    machine_id = f.read().strip()
                    identifiers.append(machine_id)
            except:
                pass

            # Hostname
            try:
                hostname = socket.gethostname()
                identifiers.append(hostname)
            except:
                pass

            # Fallback to timestamp if no hardware identifiers found
            if not identifiers:
                identifiers.append(str(int(time.time())))

            # Create hash from all identifiers
            combined = f"RNG-MINER-{'-'.join(identifiers)}"
            hash_object = hashlib.sha256(combined.encode('utf-8'))
            device_id = hash_object.hexdigest()[:8].upper()

            return device_id

        except Exception as e:
            logging.error(f"Failed to generate device ID: {e}")
            # Ultimate fallback
            return hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()

    def get_interface_mac(self, interface: str) -> str:
        """Get MAC address of specified network interface"""
        try:
            with open(f'/sys/class/net/{interface}/address', 'r') as f:
                return f.read().strip()
        except:
            # Fallback method
            import uuid
            return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])

    def setup_logging(self):
        """Configure logging system"""
        log_dir = "/opt/device-software/logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "wifi-manager.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        logging.info(f"WiFi Manager initializing - Device ID: {self.device_id}")

    def create_hostapd_config(self) -> bool:
        """Create hostapd configuration file"""
        try:
            os.makedirs(os.path.dirname(self.hostapd_config_path), exist_ok=True)

            ssid = f"RNG-Miner-{self.device_id}"

            hostapd_config = f"""# Orange Pi WiFi Hotspot Configuration
# Generated automatically - do not edit manually

interface={self.hotspot_interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.hotspot_password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Additional security settings
max_num_sta=5
wpa_group_rekey=86400
"""

            with open(self.hostapd_config_path, 'w') as f:
                f.write(hostapd_config)

            # Set proper permissions
            os.chmod(self.hostapd_config_path, 0o644)

            logging.info(f"Created hostapd config for SSID: {ssid}")
            return True

        except Exception as e:
            logging.error(f"Failed to create hostapd config: {e}")
            return False

    def create_dnsmasq_config(self) -> bool:
        """Create dnsmasq DHCP configuration file"""
        try:
            os.makedirs(os.path.dirname(self.dnsmasq_config_path), exist_ok=True)

            dnsmasq_config = f"""# Orange Pi DHCP Server Configuration
# Generated automatically - do not edit manually

interface={self.hotspot_interface}
dhcp-range={self.dhcp_range_start},{self.dhcp_range_end},255.255.255.0,24h
dhcp-option=3,{self.hotspot_ip}
dhcp-option=6,{self.hotspot_ip}
server=8.8.8.8
bind-interfaces
bogus-priv
domain-needed
"""

            with open(self.dnsmasq_config_path, 'w') as f:
                f.write(dnsmasq_config)

            # Set proper permissions
            os.chmod(self.dnsmasq_config_path, 0o644)

            logging.info(f"Created dnsmasq config for DHCP range: {self.dhcp_range_start}-{self.dhcp_range_end}")
            return True

        except Exception as e:
            logging.error(f"Failed to create dnsmasq config: {e}")
            return False

    def configure_network_interface(self) -> bool:
        """Configure network interface for hotspot mode"""
        try:
            # Bring down interface
            subprocess.run(['sudo', 'ip', 'link', 'set', self.hotspot_interface, 'down'],
                         check=True, capture_output=True)

            # Set static IP address
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', self.hotspot_interface],
                         check=True, capture_output=True)
            subprocess.run(['sudo', 'ip', 'addr', 'add', f'{self.hotspot_ip}/24', 'dev', self.hotspot_interface],
                         check=True, capture_output=True)

            # Bring up interface
            subprocess.run(['sudo', 'ip', 'link', 'set', self.hotspot_interface, 'up'],
                         check=True, capture_output=True)

            logging.info(f"Configured {self.hotspot_interface} with IP {self.hotspot_ip}")
            return True

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to configure network interface: {e}")
            return False

    def start_hostapd(self) -> bool:
        """Start hostapd service"""
        try:
            # Kill any existing hostapd processes
            self.stop_hostapd()

            # Start hostapd
            cmd = ['sudo', 'hostapd', '-B', '-P', self.hostapd_pid_file, self.hostapd_config_path]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logging.info("hostapd started successfully")
                return True
            else:
                logging.error(f"Failed to start hostapd: {result.stderr}")
                return False

        except Exception as e:
            logging.error(f"Exception starting hostapd: {e}")
            return False

    def stop_hostapd(self) -> bool:
        """Stop hostapd service"""
        try:
            # Kill by PID file if exists
            if os.path.exists(self.hostapd_pid_file):
                with open(self.hostapd_pid_file, 'r') as f:
                    pid = f.read().strip()
                    if pid:
                        subprocess.run(['sudo', 'kill', pid], capture_output=True)
                os.remove(self.hostapd_pid_file)

            # Kill any remaining hostapd processes
            subprocess.run(['sudo', 'pkill', '-f', 'hostapd'], capture_output=True)

            logging.info("hostapd stopped")
            return True

        except Exception as e:
            logging.error(f"Error stopping hostapd: {e}")
            return False

    def start_dnsmasq(self) -> bool:
        """Start dnsmasq DHCP service"""
        try:
            # Kill any existing dnsmasq processes
            self.stop_dnsmasq()

            # Start dnsmasq
            cmd = ['sudo', 'dnsmasq', '-C', self.dnsmasq_config_path, '-x', self.dnsmasq_pid_file]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logging.info("dnsmasq started successfully")
                return True
            else:
                logging.error(f"Failed to start dnsmasq: {result.stderr}")
                return False

        except Exception as e:
            logging.error(f"Exception starting dnsmasq: {e}")
            return False

    def stop_dnsmasq(self) -> bool:
        """Stop dnsmasq DHCP service"""
        try:
            # Kill by PID file if exists
            if os.path.exists(self.dnsmasq_pid_file):
                with open(self.dnsmasq_pid_file, 'r') as f:
                    pid = f.read().strip()
                    if pid:
                        subprocess.run(['sudo', 'kill', pid], capture_output=True)
                os.remove(self.dnsmasq_pid_file)

            # Kill any remaining dnsmasq processes
            subprocess.run(['sudo', 'pkill', '-f', 'dnsmasq'], capture_output=True)

            logging.info("dnsmasq stopped")
            return True

        except Exception as e:
            logging.error(f"Error stopping dnsmasq: {e}")
            return False

    def is_hotspot_active(self) -> bool:
        """Check if hotspot is currently active"""
        try:
            # Check if hostapd is running
            if os.path.exists(self.hostapd_pid_file):
                with open(self.hostapd_pid_file, 'r') as f:
                    pid = f.read().strip()
                    if pid:
                        try:
                            subprocess.run(['ps', '-p', pid], check=True, capture_output=True)
                            return True
                        except subprocess.CalledProcessError:
                            pass

            # Check for hostapd process
            result = subprocess.run(['pgrep', '-f', 'hostapd'], capture_output=True)
            return result.returncode == 0

        except Exception as e:
            logging.error(f"Error checking hotspot status: {e}")
            return False

    def get_connected_clients(self) -> List[Dict]:
        """Get list of connected clients"""
        clients = []
        try:
            # Read DHCP leases file
            leases_file = "/var/lib/dhcp/dhcpd.leases"
            if os.path.exists(leases_file):
                with open(leases_file, 'r') as f:
                    content = f.read()
                    # Parse DHCP leases (simplified)
                    # In production, would need more robust parsing

            # Alternative: parse dnsmasq leases
            dnsmasq_leases = "/var/lib/dhcp/dnsmasq.leases"
            if os.path.exists(dnsmasq_leases):
                with open(dnsmasq_leases, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            clients.append({
                                'ip': parts[2],
                                'mac': parts[1],
                                'hostname': parts[3] if len(parts) > 3 else 'unknown',
                                'lease_time': parts[0]
                            })

        except Exception as e:
            logging.error(f"Error getting connected clients: {e}")

        return clients

    def start_hotspot(self) -> bool:
        """Start WiFi hotspot with full configuration"""
        try:
            logging.info("Starting WiFi hotspot...")

            # Save current configuration
            self.save_config()

            # Create configuration files
            if not self.create_hostapd_config():
                return False

            if not self.create_dnsmasq_config():
                return False

            # Configure network interface
            if not self.configure_network_interface():
                return False

            # Start services
            if not self.start_hostapd():
                return False

            # Wait a moment for hostapd to stabilize
            time.sleep(2)

            if not self.start_dnsmasq():
                self.stop_hostapd()
                return False

            self.hotspot_active = True

            ssid = f"RNG-Miner-{self.device_id}"
            logging.info(f"WiFi hotspot '{ssid}' started successfully")
            logging.info(f"Hotspot IP: {self.hotspot_ip}")
            logging.info(f"DHCP range: {self.dhcp_range_start} - {self.dhcp_range_end}")

            return True

        except Exception as e:
            logging.error(f"Failed to start hotspot: {e}")
            self.stop_hotspot()
            return False

    def stop_hotspot(self) -> bool:
        """Stop WiFi hotspot"""
        try:
            logging.info("Stopping WiFi hotspot...")

            # Stop services
            self.stop_dnsmasq()
            self.stop_hostapd()

            # Reset network interface (optional)
            try:
                subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', self.hotspot_interface],
                             capture_output=True)
                subprocess.run(['sudo', 'ip', 'link', 'set', self.hotspot_interface, 'down'],
                             capture_output=True)
            except:
                pass

            self.hotspot_active = False
            logging.info("WiFi hotspot stopped")

            return True

        except Exception as e:
            logging.error(f"Error stopping hotspot: {e}")
            return False

    def restart_hotspot(self) -> bool:
        """Restart WiFi hotspot"""
        logging.info("Restarting WiFi hotspot...")

        if not self.stop_hotspot():
            logging.error("Failed to stop hotspot for restart")
            return False

        # Wait a moment between stop and start
        time.sleep(3)

        return self.start_hotspot()

    def get_hotspot_status(self) -> Dict:
        """Get comprehensive hotspot status information"""
        return {
            'active': self.is_hotspot_active(),
            'device_id': self.device_id,
            'ssid': f"RNG-Miner-{self.device_id}",
            'ip_address': self.hotspot_ip,
            'dhcp_range': f"{self.dhcp_range_start} - {self.dhcp_range_end}",
            'connected_clients': self.get_connected_clients(),
            'interface': self.hotspot_interface,
            'password': self.hotspot_password,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

def main():
    """Main entry point for WiFi manager"""
    import argparse

    parser = argparse.ArgumentParser(description='Orange Pi WiFi Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'],
                       help='Action to perform')

    args = parser.parse_args()

    wifi_manager = WiFiManager()

    try:
        if args.action == 'start':
            success = wifi_manager.start_hotspot()
            sys.exit(0 if success else 1)
        elif args.action == 'stop':
            success = wifi_manager.stop_hotspot()
            sys.exit(0 if success else 1)
        elif args.action == 'restart':
            success = wifi_manager.restart_hotspot()
            sys.exit(0 if success else 1)
        elif args.action == 'status':
            status = wifi_manager.get_hotspot_status()
            print(json.dumps(status, indent=2))
            sys.exit(0)
    except KeyboardInterrupt:
        wifi_manager.stop_hotspot()
    except Exception as e:
        logging.error(f"WiFi Manager error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
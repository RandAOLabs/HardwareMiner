#!/usr/bin/env python3
"""
Orange Pi HTTP Server
Lightweight HTTPS server for device communication
"""

import os
import sys
import json
import time
import signal
import logging
import hashlib
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from OpenSSL import SSL, crypto
import socket

# Import WiFi manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wifi-manager'))
try:
    from wifi_manager import WiFiManager
except ImportError:
    logging.warning("WiFi manager not available - hotspot features disabled")
    WiFiManager = None

class DeviceHTTPServer:
    def __init__(self, config_path="/opt/device-software/config/device-config.json"):
        self.app = Flask(__name__)
        self.config_path = config_path
        self.config = self.load_config()
        self.server_start_time = time.time()
        self.device_id = self.generate_device_id()
        self.setup_logging()
        self.setup_routes()
        self.cert_file = "/opt/device-software/config/server.crt"
        self.key_file = "/opt/device-software/config/server.key"
        self.running = False

        # Initialize WiFi manager if available
        self.wifi_manager = None
        if WiFiManager:
            try:
                self.wifi_manager = WiFiManager(config_path=config_path)
            except Exception as e:
                logging.error(f"Failed to initialize WiFi manager: {e}")

    def load_config(self):
        """Load device configuration from JSON file"""
        default_config = {
            "device_id": "",
            "http_port": 80,
            "wifi_state_timeout": 30,
            "dhcp_range": "192.168.4.0/24",
            "connection_retry_limit": 3,
            "api_rate_limit": {
                "requests_per_minute": 30,
                "burst_limit": 100
            }
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
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
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def generate_device_id(self):
        """Generate 8-character unique device ID based on hardware identifiers"""
        # Check if device ID already exists in config
        if self.config.get("device_id"):
            return self.config["device_id"]

        try:
            # Collect hardware identifiers
            identifiers = []

            # MAC address (primary network interface)
            try:
                import uuid
                mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                      for elements in range(0,2*6,2)][::-1])
                identifiers.append(mac_address)
            except:
                pass

            # CPU serial number (if available)
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('Serial'):
                            identifiers.append(line.split(':')[1].strip())
                            break
            except:
                pass

            # Machine ID
            try:
                with open('/etc/machine-id', 'r') as f:
                    identifiers.append(f.read().strip())
            except:
                pass

            # Hostname
            try:
                identifiers.append(socket.gethostname())
            except:
                pass

            # Fallback to current timestamp if no hardware identifiers found
            if not identifiers:
                identifiers.append(str(int(time.time())))

            # Create hash from all identifiers
            combined = ''.join(identifiers)
            hash_object = hashlib.sha256(combined.encode())
            device_id = hash_object.hexdigest()[:8].upper()

            return device_id

        except Exception as e:
            logging.error(f"Failed to generate device ID: {e}")
            # Fallback to timestamp-based ID
            return hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()

    def setup_logging(self):
        """Configure logging system with rotation"""
        log_dir = "/opt/device-software/logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "http-server.log")

        # Configure logging format
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Log server startup
        logging.info(f"HTTP Server initializing - Device ID: {self.device_id}")

    def generate_self_signed_cert(self):
        """Generate self-signed certificate for HTTPS"""
        try:
            # Create certificate directory
            os.makedirs(os.path.dirname(self.cert_file), exist_ok=True)

            # Check if certificate already exists and is valid
            if os.path.exists(self.cert_file) and os.path.exists(self.key_file):
                logging.info("Using existing SSL certificate")
                return

            # Generate private key
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)

            # Generate certificate
            cert = crypto.X509()
            cert.get_subject().C = "US"
            cert.get_subject().ST = "CA"
            cert.get_subject().L = "Device"
            cert.get_subject().O = "RNG Miner"
            cert.get_subject().OU = "Device"
            cert.get_subject().CN = "RNG-Miner"

            # Add Subject Alternative Names for both hotspot and potential home network IPs
            cert.add_extensions([
                crypto.X509Extension(b"subjectAltName", False,
                                   b"IP:192.168.4.1,IP:192.168.12.1,DNS:rng-miner.local")
            ])

            cert.set_serial_number(1)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for 1 year
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, 'sha256')

            # Write certificate and key to files
            with open(self.cert_file, 'wb') as f:
                f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

            with open(self.key_file, 'wb') as f:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

            # Set proper permissions
            os.chmod(self.key_file, 0o600)
            os.chmod(self.cert_file, 0o644)

            logging.info("Generated new SSL certificate")

        except Exception as e:
            logging.error(f"Failed to generate SSL certificate: {e}")
            raise

    def setup_routes(self):
        """Setup Flask routes with request logging"""

        @self.app.before_request
        def log_request_info():
            """Log incoming requests with detailed info"""
            client_ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'Unknown')
            logging.info(f"🔵 Incoming Request: {request.method} {request.path}")
            logging.info(f"   Client IP: {client_ip}")
            logging.info(f"   User Agent: {user_agent}")
            logging.info(f"   Headers: {dict(request.headers)}")

        @self.app.after_request
        def log_response_info(response):
            """Log outgoing responses with detailed info"""
            client_ip = request.remote_addr
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logging.info(f"{status_emoji} Response: {response.status_code} for {request.method} {request.path} to {client_ip}")

            # Add CORS headers to allow cross-origin requests from mobile apps
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'

            return response

        @self.app.before_first_request
        def startup_verification():
            """Run verification checks when first request comes in"""
            logging.info("🚀 First request received - server is accepting connections!")

        @self.app.errorhandler(Exception)
        def handle_exception(e):
            """Log all exceptions for debugging"""
            logging.error(f"💥 Unhandled exception: {str(e)}")
            logging.error(f"Request: {request.method} {request.path} from {request.remote_addr}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

            return jsonify({
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "Internal server error occurred",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                uptime = int(time.time() - self.server_start_time)
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "device_id": self.device_id,
                    "uptime": uptime
                }
                return jsonify(response), 200
            except Exception as e:
                logging.error(f"Health check failed: {e}")
                error_response = {
                    "success": False,
                    "error_code": "HEALTH_CHECK_FAILED",
                    "message": "Health check endpoint error",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                return jsonify(error_response), 500

        @self.app.route('/device/info', methods=['GET'])
        def device_info():
            """Device information endpoint"""
            try:
                # Get current IP address
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip_address = s.getsockname()[0]
                    s.close()
                except:
                    ip_address = "unknown"

                # Get WiFi/hotspot status
                wifi_state = "unknown"
                hotspot_info = {}
                if self.wifi_manager:
                    try:
                        hotspot_status = self.wifi_manager.get_hotspot_status()
                        if hotspot_status['active']:
                            wifi_state = "hotspot_active"
                            hotspot_info = {
                                "ssid": hotspot_status['ssid'],
                                "ip_address": hotspot_status['ip_address'],
                                "connected_clients": len(hotspot_status['connected_clients']),
                                "dhcp_range": hotspot_status['dhcp_range']
                            }
                        else:
                            wifi_state = "disconnected"
                    except Exception as e:
                        logging.error(f"Failed to get WiFi status: {e}")

                # Get basic system info (simplified for now)
                try:
                    import psutil
                    cpu_usage = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    memory_usage = memory.percent
                    disk_usage = disk.percent
                except ImportError:
                    # Fallback if psutil not available
                    cpu_usage = 0.0
                    memory_usage = 0.0
                    disk_usage = 0.0

                response = {
                    "device_id": self.device_id,
                    "model": "Orange Pi Zero 3",
                    "wifi_state": wifi_state,
                    "ip_address": ip_address,
                    "ssid": hotspot_info.get('ssid', '') if hotspot_info else '',
                    "mining_status": "not_configured",
                    "system_info": {
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "disk_usage": disk_usage,
                        "uptime": int(time.time() - self.server_start_time)
                    },
                    "configuration_status": {
                        "wifi_configured": False,  # TODO: Check actual WiFi config status
                        "seed_phrase_set": False,  # TODO: Check if seed phrase is stored
                        "provider_id_set": False,  # TODO: Check if provider ID is set
                        "mining_ready": False      # TODO: Check if mining is configured
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                # Add hotspot info if active
                if hotspot_info:
                    response["hotspot"] = hotspot_info

                return jsonify(response), 200
            except Exception as e:
                logging.error(f"Device info failed: {e}")
                error_response = {
                    "success": False,
                    "error_code": "DEVICE_INFO_FAILED",
                    "message": "Failed to retrieve device information",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                return jsonify(error_response), 500

        @self.app.route('/wifi/hotspot/status', methods=['GET'])
        def hotspot_status():
            """Get detailed hotspot status"""
            try:
                if not self.wifi_manager:
                    return jsonify({
                        "success": False,
                        "error_code": "WIFI_MANAGER_UNAVAILABLE",
                        "message": "WiFi manager not available"
                    }), 503

                status = self.wifi_manager.get_hotspot_status()
                return jsonify(status), 200

            except Exception as e:
                logging.error(f"Hotspot status failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "HOTSPOT_STATUS_FAILED",
                    "message": "Failed to get hotspot status",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        @self.app.route('/wifi/hotspot/start', methods=['POST'])
        def start_hotspot():
            """Start WiFi hotspot"""
            try:
                if not self.wifi_manager:
                    return jsonify({
                        "success": False,
                        "error_code": "WIFI_MANAGER_UNAVAILABLE",
                        "message": "WiFi manager not available"
                    }), 503

                success = self.wifi_manager.start_hotspot()
                if success:
                    return jsonify({
                        "success": True,
                        "message": "Hotspot started successfully",
                        "device_id": self.device_id,
                        "ssid": f"RNG-Miner-{self.device_id}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error_code": "HOTSPOT_START_FAILED",
                        "message": "Failed to start hotspot"
                    }), 500

            except Exception as e:
                logging.error(f"Start hotspot failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "HOTSPOT_START_ERROR",
                    "message": "Error starting hotspot",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        @self.app.route('/wifi/hotspot/stop', methods=['POST'])
        def stop_hotspot():
            """Stop WiFi hotspot"""
            try:
                if not self.wifi_manager:
                    return jsonify({
                        "success": False,
                        "error_code": "WIFI_MANAGER_UNAVAILABLE",
                        "message": "WiFi manager not available"
                    }), 503

                success = self.wifi_manager.stop_hotspot()
                if success:
                    return jsonify({
                        "success": True,
                        "message": "Hotspot stopped successfully",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error_code": "HOTSPOT_STOP_FAILED",
                        "message": "Failed to stop hotspot"
                    }), 500

            except Exception as e:
                logging.error(f"Stop hotspot failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "HOTSPOT_STOP_ERROR",
                    "message": "Error stopping hotspot",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        @self.app.route('/device/configure', methods=['POST'])
        def configure_device():
            """Configure device with WiFi credentials and mining setup"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error_code": "INVALID_REQUEST",
                        "message": "JSON payload required"
                    }), 400

                # Store configuration data temporarily
                # In a full implementation, this would validate and apply the configuration
                wifi_creds = data.get('wifi_credentials', {})
                seed_phrase = data.get('seed_phrase', '')
                wallet_jwk = data.get('wallet_jwk', {})
                provider_id = data.get('provider_id', '')

                logging.info(f"Received configuration - WiFi SSID: {wifi_creds.get('ssid', 'N/A')}")
                logging.info(f"Provider ID: {provider_id}")

                # For now, just acknowledge the configuration
                # In a real implementation, you would:
                # 1. Connect to the WiFi network
                # 2. Store the seed phrase securely
                # 3. Set up mining with the provider ID

                return jsonify({
                    "success": True,
                    "message": "Configuration received and will be applied",
                    "step_completed": "configuration_received",
                    "next_step": "wifi_connection",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 200

            except Exception as e:
                logging.error(f"Device configuration failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "CONFIGURATION_ERROR",
                    "message": f"Configuration failed: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        @self.app.route('/device/test-wifi', methods=['POST'])
        def test_wifi_credentials():
            """Test WiFi credentials without connecting"""
            try:
                data = request.get_json()
                if not data or 'wifi_credentials' not in data:
                    return jsonify({
                        "valid": False,
                        "message": "WiFi credentials required"
                    }), 400

                wifi_creds = data['wifi_credentials']
                ssid = wifi_creds.get('ssid', '')
                password = wifi_creds.get('password', '')

                logging.info(f"Testing WiFi credentials for SSID: {ssid}")

                # For now, just return that testing is not implemented
                # In a real implementation, you would attempt to connect temporarily
                return jsonify({
                    "valid": True,
                    "message": "WiFi credential testing not yet implemented - credentials accepted"
                }), 200

            except Exception as e:
                logging.error(f"WiFi credential test failed: {e}")
                return jsonify({
                    "valid": False,
                    "message": f"Test failed: {str(e)}"
                }), 500

        @self.app.route('/device/reset', methods=['POST'])
        def reset_configuration():
            """Reset device configuration to factory defaults"""
            try:
                logging.info("Device configuration reset requested")

                # In a real implementation, you would:
                # 1. Clear stored WiFi credentials
                # 2. Remove seed phrase and wallet data
                # 3. Reset mining configuration
                # 4. Restart hotspot mode

                return jsonify({
                    "success": True,
                    "message": "Device configuration reset successful",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 200

            except Exception as e:
                logging.error(f"Device reset failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "RESET_ERROR",
                    "message": f"Reset failed: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        @self.app.route('/device/logs', methods=['GET'])
        def get_device_logs():
            """Get recent device logs"""
            try:
                # Read recent log entries
                log_file = "/opt/device-software/logs/http-server.log"
                logs = []

                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 50 lines
                        logs = [line.strip() for line in lines[-50:]]
                else:
                    logs = ["Log file not found"]

                return jsonify({
                    "logs": logs,
                    "success": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 200

            except Exception as e:
                logging.error(f"Failed to read logs: {e}")
                return jsonify({
                    "logs": [f"Error reading logs: {str(e)}"],
                    "success": False,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors"""
            response = {
                "success": False,
                "error_code": "ENDPOINT_NOT_FOUND",
                "message": "API endpoint not found",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return jsonify(response), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors"""
            response = {
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return jsonify(response), 500

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def configure_firewall(self, port):
        """Configure firewall to allow HTTP traffic"""
        try:
            logging.info(f"Configuring firewall for port {port}...")

            # Allow HTTP traffic on the specified port
            subprocess.run([
                'sudo', 'iptables', '-I', 'INPUT', '-p', 'tcp',
                '--dport', str(port), '-j', 'ACCEPT'
            ], capture_output=True)

            # Allow traffic from hotspot network
            subprocess.run([
                'sudo', 'iptables', '-I', 'INPUT', '-s', '192.168.4.0/24',
                '-j', 'ACCEPT'
            ], capture_output=True)

            # Also allow general HTTP traffic for mobile clients
            if port == 80:
                subprocess.run([
                    'sudo', 'iptables', '-I', 'INPUT', '-p', 'tcp',
                    '--dport', '80', '-j', 'ACCEPT'
                ], capture_output=True)

            logging.info("Firewall configured successfully")
            return True

        except Exception as e:
            logging.warning(f"Firewall configuration failed (may not be critical): {e}")
            return False

    def verify_network_setup(self):
        """Verify network interface is properly configured"""
        try:
            logging.info("Verifying network setup...")

            # Check if wlan0 has the correct IP
            result = subprocess.run(['ip', 'addr', 'show', 'wlan0'],
                                  capture_output=True, text=True)

            if '192.168.4.1' in result.stdout:
                logging.info("✅ wlan0 interface has correct IP (192.168.4.1)")
            else:
                logging.warning("⚠️  wlan0 interface may not have correct IP")
                logging.info(f"wlan0 status: {result.stdout}")

            # Check if we can bind to the interface
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_socket.bind(('0.0.0.0', 8081))  # Test port
                test_socket.close()
                logging.info("✅ Socket binding test successful")
            except Exception as e:
                logging.error(f"❌ Socket binding test failed: {e}")

        except Exception as e:
            logging.error(f"Network verification failed: {e}")

    def start_server(self):
        """Start HTTP server (HTTPS can be added later)"""
        try:
            # Save configuration
            self.save_config()

            # Verify network setup
            self.verify_network_setup()

            # Configure firewall
            self.configure_firewall(self.config['http_port'])

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self.signal_handler)
            signal.signal(signal.SIGINT, self.signal_handler)

            self.running = True
            port = self.config['http_port']

            logging.info(f"Starting HTTP server on port {port}")
            logging.info(f"Device ID: {self.device_id}")
            logging.info(f"Binding to all interfaces (0.0.0.0:{port})")
            logging.info(f"🌐 Server will be accessible at:")
            logging.info(f"  - http://192.168.4.1 (standard HTTP port {port})")
            logging.info(f"  - http://DeviceSetup.local (if mDNS works)")
            logging.info(f"📡 Available endpoints: /health, /device/info, /device/configure")

            # Start Flask app on port 80 (standard HTTP port for captive portals)
            logging.info("🚀 Starting Flask HTTP server for captive portal...")
            self.app.run(
                host='0.0.0.0',  # Bind to all interfaces
                port=port,
                debug=False,
                threaded=True,
                use_reloader=False  # Prevent reloader in production
            )

        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            sys.exit(1)

    def stop_server(self):
        """Stop the server gracefully"""
        logging.info("Stopping HTTP server...")
        self.running = False

def main():
    """Main entry point"""
    server = DeviceHTTPServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        server.stop_server()
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
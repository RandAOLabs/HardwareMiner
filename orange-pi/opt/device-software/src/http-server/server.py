#!/usr/bin/env python3
"""
Enhanced Orange Pi HTTP Server
Complete implementation with configuration management and API endpoints
Based on working old-bad-way patterns
"""

import os
import sys
import json
import time
import signal
import logging
import hashlib
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import socket

# Configuration paths
CONFIG_DIR = Path("/opt/device-software/config")
DATA_DIR = Path("/opt/device-software/data")
LOG_DIR = Path("/opt/device-software/logs")
MINING_DIR = Path("/opt/mining/Randomness-Provider/docker-compose")

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
MINING_DIR.mkdir(parents=True, exist_ok=True)

class EnhancedDeviceServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for mobile app access

        self.config_file = CONFIG_DIR / "device_config.json"
        self.mining_config_file = CONFIG_DIR / "mining_config.json"
        self.wifi_config_file = CONFIG_DIR / "wifi_config.json"
        self.env_file = MINING_DIR / ".env"

        self.server_start_time = time.time()
        self.device_id = self.get_device_id()
        self.setup_logging()
        self.setup_routes()

    def setup_logging(self):
        """Configure logging system"""
        log_file = LOG_DIR / "http-server.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Enhanced server initializing - Device ID: {self.device_id}")

    def get_device_id(self):
        """Generate or retrieve device ID"""
        device_id_file = DATA_DIR / 'device_id'

        if device_id_file.exists():
            with open(device_id_file, 'r') as f:
                return f.read().strip()

        # Generate new device ID
        identifiers = []

        try:
            # Get MAC address
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,48,8)])
            identifiers.append(mac)
        except:
            pass

        try:
            # Get machine ID
            with open('/etc/machine-id', 'r') as f:
                identifiers.append(f.read().strip())
        except:
            pass

        try:
            # Get hostname
            identifiers.append(socket.gethostname())
        except:
            pass

        # Create hash from identifiers
        combined = '-'.join(identifiers)
        if not combined:
            combined = f"rng-miner-{int(time.time())}"

        device_hash = hashlib.sha256(combined.encode()).hexdigest()
        device_id = device_hash[:8].upper()

        # Save device ID
        with open(device_id_file, 'w') as f:
            f.write(device_id)

        self.logger.info(f"Generated device ID: {device_id}")
        return device_id

    def load_device_config(self):
        """Load current device configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                # Merge with mining config if available
                if self.mining_config_file.exists():
                    with open(self.mining_config_file, 'r') as f:
                        mining_config = json.load(f)
                        config.update(mining_config)

                # Merge with wifi config if available
                if self.wifi_config_file.exists():
                    with open(self.wifi_config_file, 'r') as f:
                        wifi_config = json.load(f)
                        config.update(wifi_config)

                return config
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load device config: {e}")
            return {}

    def save_device_config(self, config_data):
        """Save device configuration"""
        try:
            # Save to main config file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Also update .env file for mining if relevant fields exist
            if any(key in config_data for key in ['seed_phrase', 'provider_id', 'wallet_json']):
                self.update_env_file(config_data)

            self.logger.info("Device configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save device config: {e}")
            return False

    def update_env_file(self, config_data):
        """Update .env file with mining configuration"""
        try:
            env_content = []

            # Add log level
            log_level = config_data.get('log_console_level', '3')
            env_content.append(f'LOG_CONSOLE_LEVEL={log_level}')

            # Add seed phrase
            seed_phrase = config_data.get('seed_phrase', '')
            if seed_phrase:
                env_content.append(f'SEED_PHRASE="{seed_phrase}"')

            # Add provider ID
            provider_id = config_data.get('provider_id', '')
            if provider_id:
                env_content.append(f'PROVIDER_ID="{provider_id}"')

            # Add wallet JSON
            wallet_json = config_data.get('wallet_json', '')
            if wallet_json:
                if isinstance(wallet_json, dict):
                    wallet_json = json.dumps(wallet_json)
                env_content.append(f"WALLET_JSON='{wallet_json}'")

            # Write to .env file
            with open(self.env_file, 'w') as f:
                f.write('\n'.join(env_content))

            self.logger.info("Mining .env file updated")

        except Exception as e:
            self.logger.error(f"Failed to update .env file: {e}")

    def get_system_info(self):
        """Get current system information"""
        try:
            # Get current IP
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            ip_address = result.stdout.strip().split()[0] if result.stdout.strip() else "unknown"
        except:
            ip_address = "unknown"

        # Check WiFi connection status (simplified)
        wifi_connected = False
        wifi_ssid = None
        try:
            # Try to get WiFi info
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                wifi_ssid = result.stdout.strip()
                wifi_connected = True
        except:
            pass

        return {
            'device_id': self.device_id,
            'ip_address': ip_address,
            'wifi_connected': wifi_connected,
            'wifi_ssid': wifi_ssid or '',
            'uptime': int(time.time() - self.server_start_time),
            'timestamp': datetime.now().isoformat()
        }

    def setup_routes(self):
        """Setup all Flask routes"""

        @self.app.before_request
        def log_request():
            """Log all incoming requests"""
            client_ip = request.remote_addr
            self.logger.info(f"🔵 {request.method} {request.path} from {client_ip}")

        @self.app.after_request
        def add_cors_headers(response):
            """Add CORS headers and log responses"""
            client_ip = request.remote_addr
            status_emoji = "✅" if response.status_code < 400 else "❌"
            self.logger.info(f"{status_emoji} {response.status_code} for {request.method} {request.path} to {client_ip}")

            # Ensure CORS headers are set
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
            return response

        # Health check endpoint
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint - matches mobile app expectations"""
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
                self.logger.error(f"Health check failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "HEALTH_CHECK_FAILED",
                    "message": "Health check endpoint error",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        # Device info endpoint - matches mobile app expectations
        @self.app.route('/device/info', methods=['GET'])
        def device_info():
            """Device information endpoint"""
            try:
                system_info = self.get_system_info()
                config_data = self.load_device_config()

                response = {
                    "device_id": self.device_id,
                    "model": "Orange Pi Zero 3",
                    "wifi_state": "connected" if system_info['wifi_connected'] else "disconnected",
                    "ip_address": system_info['ip_address'],
                    "ssid": system_info['wifi_ssid'],
                    "mining_status": "configured" if config_data.get('seed_phrase') else "not_configured",
                    "uptime": system_info['uptime'],
                    "timestamp": system_info['timestamp'],
                    "configuration_status": {
                        "wifi_configured": system_info['wifi_connected'],
                        "seed_phrase_set": bool(config_data.get('seed_phrase')),
                        "provider_id_set": bool(config_data.get('provider_id')),
                        "wallet_json_set": bool(config_data.get('wallet_json')),
                        "mining_ready": bool(config_data.get('seed_phrase') and config_data.get('provider_id'))
                    }
                }
                return jsonify(response), 200
            except Exception as e:
                self.logger.error(f"Device info failed: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "DEVICE_INFO_FAILED",
                    "message": "Failed to retrieve device information",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500

        # Configuration API endpoints - matches old-bad-way patterns
        @self.app.route('/api/env-vars', methods=['GET'])
        def get_env_vars():
            """Get environment variables - matches old-bad-way API"""
            try:
                config_data = self.load_device_config()

                env_vars = {
                    'SEED_PHRASE': config_data.get('seed_phrase', ''),
                    'PROVIDER_ID': config_data.get('provider_id', ''),
                    'WALLET_JSON': config_data.get('wallet_json', ''),
                    'LOG_CONSOLE_LEVEL': config_data.get('log_console_level', '3'),
                    'NETWORK_IP': config_data.get('network_ip', ''),
                    'NETWORK_MODE': config_data.get('network_mode', '')
                }

                return jsonify(env_vars), 200
            except Exception as e:
                self.logger.error(f"Get env vars failed: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get configuration status - matches old-bad-way API"""
            try:
                config_data = self.load_device_config()

                status = {
                    'seedPhrase': bool(config_data.get('seed_phrase', '').strip()),
                    'providerId': bool(config_data.get('provider_id', '').strip()),
                    'walletJson': bool(config_data.get('wallet_json', '').strip())
                }

                return jsonify(status), 200
            except Exception as e:
                self.logger.error(f"Get status failed: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/set-seed-phrase', methods=['POST', 'OPTIONS'])
        def set_seed_phrase():
            """Set seed phrase - matches old-bad-way API"""
            if request.method == 'OPTIONS':
                return '', 200

            try:
                data = request.get_json()
                seed_phrase = data.get('seed_phrase', '').strip()

                if not seed_phrase:
                    return jsonify({'error': 'seed_phrase is required'}), 400

                config_data = self.load_device_config()
                config_data['seed_phrase'] = seed_phrase
                config_data['timestamp'] = datetime.now().isoformat()

                if self.save_device_config(config_data):
                    return jsonify({'success': True, 'seed_phrase_set': True}), 200
                else:
                    return jsonify({'error': 'Failed to save seed_phrase'}), 500

            except Exception as e:
                self.logger.error(f"Set seed phrase failed: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/set-provider-id', methods=['POST', 'OPTIONS'])
        def set_provider_id():
            """Set provider ID - matches old-bad-way API"""
            if request.method == 'OPTIONS':
                return '', 200

            try:
                data = request.get_json()
                provider_id = data.get('provider_id', '').strip()

                if not provider_id:
                    return jsonify({'error': 'provider_id is required'}), 400

                config_data = self.load_device_config()
                config_data['provider_id'] = provider_id
                config_data['timestamp'] = datetime.now().isoformat()

                if self.save_device_config(config_data):
                    return jsonify({'success': True, 'provider_id': provider_id}), 200
                else:
                    return jsonify({'error': 'Failed to save provider_id'}), 500

            except Exception as e:
                self.logger.error(f"Set provider ID failed: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/set-wallet-json', methods=['POST', 'OPTIONS'])
        def set_wallet_json():
            """Set wallet JSON - matches old-bad-way API"""
            if request.method == 'OPTIONS':
                return '', 200

            try:
                data = request.get_json()
                wallet_json = data.get('wallet_json', '').strip()

                if not wallet_json:
                    return jsonify({'error': 'wallet_json is required'}), 400

                # Validate JSON if it's a string
                if isinstance(wallet_json, str):
                    try:
                        json.loads(wallet_json)
                    except json.JSONDecodeError:
                        return jsonify({'error': 'Invalid wallet_json format'}), 400
                elif isinstance(wallet_json, dict):
                    wallet_json = json.dumps(wallet_json)

                config_data = self.load_device_config()
                config_data['wallet_json'] = wallet_json
                config_data['timestamp'] = datetime.now().isoformat()

                if self.save_device_config(config_data):
                    return jsonify({'success': True, 'wallet_json_set': True}), 200
                else:
                    return jsonify({'error': 'Failed to save wallet_json'}), 500

            except Exception as e:
                self.logger.error(f"Set wallet JSON failed: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/set-all-config', methods=['POST', 'OPTIONS'])
        def set_all_config():
            """Set all configuration values at once - matches old-bad-way API"""
            if request.method == 'OPTIONS':
                return '', 200

            try:
                data = request.get_json()
                config_data = self.load_device_config()

                # Update with provided values
                if 'seed_phrase' in data and data['seed_phrase']:
                    config_data['seed_phrase'] = data['seed_phrase'].strip()

                if 'provider_id' in data and data['provider_id']:
                    config_data['provider_id'] = data['provider_id'].strip()

                if 'wallet_json' in data and data['wallet_json']:
                    wallet_json = data['wallet_json']
                    if isinstance(wallet_json, str):
                        try:
                            json.loads(wallet_json)
                        except json.JSONDecodeError:
                            return jsonify({'error': 'Invalid wallet_json format'}), 400
                    elif isinstance(wallet_json, dict):
                        wallet_json = json.dumps(wallet_json)
                    config_data['wallet_json'] = wallet_json

                config_data['timestamp'] = datetime.now().isoformat()

                if self.save_device_config(config_data):
                    return jsonify({
                        'success': True,
                        'seed_phrase_set': bool(config_data.get('seed_phrase')),
                        'provider_id_set': bool(config_data.get('provider_id')),
                        'wallet_json_set': bool(config_data.get('wallet_json'))
                    }), 200
                else:
                    return jsonify({'error': 'Failed to save configuration'}), 500

            except Exception as e:
                self.logger.error(f"Set all config failed: {e}")
                return jsonify({'error': str(e)}), 500

        # WiFi setup endpoints
        @self.app.route('/setup/wifi', methods=['POST'])
        def setup_wifi():
            """Setup WiFi connection"""
            try:
                data = request.get_json()

                if not data or 'ssid' not in data or 'password' not in data:
                    return jsonify({
                        "success": False,
                        "error_code": "INVALID_REQUEST",
                        "message": "SSID and password are required"
                    }), 400

                ssid = data['ssid'].strip()
                password = data['password']

                if not ssid:
                    return jsonify({
                        "success": False,
                        "error_code": "INVALID_SSID",
                        "message": "SSID cannot be empty"
                    }), 400

                self.logger.info(f"Setting up WiFi connection to: {ssid}")

                # Save WiFi credentials
                wifi_config = {
                    "ssid": ssid,
                    "password": password,
                    "timestamp": datetime.now().isoformat()
                }

                with open(self.wifi_config_file, 'w') as f:
                    json.dump(wifi_config, f)

                # Trigger WiFi connection in background thread
                def connect_wifi_background():
                    try:
                        self.logger.info(f"Background: Initiating WiFi connection to {ssid}")
                        subprocess.run([
                            'python3',
                            '/opt/device-software/scripts/wifi_connect.py',
                            ssid,
                            password
                        ], timeout=60)
                    except Exception as e:
                        self.logger.error(f"Background WiFi connection failed: {e}")

                thread = threading.Thread(target=connect_wifi_background, daemon=True)
                thread.start()

                return jsonify({
                    "success": True,
                    "message": "WiFi connection initiated"
                }), 200

            except Exception as e:
                self.logger.error(f"WiFi setup error: {e}")
                return jsonify({
                    "success": False,
                    "error_code": "SETUP_FAILED",
                    "message": str(e)
                }), 500

        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "error_code": "ENDPOINT_NOT_FOUND",
                "message": "API endpoint not found",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500

    def start_server(self):
        """Start the HTTP server"""
        try:
            port = 80  # Standard HTTP port for captive portal

            self.logger.info(f"🚀 Starting Enhanced Orange Pi HTTP Server on port {port}")
            self.logger.info(f"Device ID: {self.device_id}")
            self.logger.info(f"Available endpoints:")
            self.logger.info(f"  - /health")
            self.logger.info(f"  - /device/info")
            self.logger.info(f"  - /api/env-vars")
            self.logger.info(f"  - /api/status")
            self.logger.info(f"  - /api/set-seed-phrase")
            self.logger.info(f"  - /api/set-provider-id")
            self.logger.info(f"  - /api/set-wallet-json")
            self.logger.info(f"  - /api/set-all-config")
            self.logger.info(f"  - /setup/wifi")

            self.app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                threaded=True,
                use_reloader=False
            )

        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    server = EnhancedDeviceServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        server.logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        server.logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
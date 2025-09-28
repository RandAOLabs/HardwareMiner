#!/usr/bin/env python3
"""
Super Simple Flask HTTP Server for RNG-Miner
Just serves basic API endpoints without complexity
"""

import os
import json
import hashlib
import time
import socket
from datetime import datetime
from flask import Flask, request, jsonify

# Create Flask app
app = Flask(__name__)

def get_device_id():
    """Generate a simple device ID"""
    try:
        hostname = socket.gethostname()
        mac = hex(hash(hostname))[-8:]
        return f"RNG{mac}".upper()
    except:
        return "RNG12345678"

def get_system_info():
    """Get basic system information"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'disk_usage': disk.percent,
            'uptime': time.time()
        }
    except:
        return {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'uptime': time.time()
        }

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    print(f"📡 Health check request from {request.remote_addr}")

    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "device_id": get_device_id(),
        "server": "simple-flask",
        "ip": "192.168.4.1"
    }

    print(f"✅ Responding with: {response}")
    return jsonify(response)

@app.route('/device/info', methods=['GET'])
def device_info():
    """Device information endpoint"""
    print(f"📡 Device info request from {request.remote_addr}")

    system_info = get_system_info()

    response = {
        "device_id": get_device_id(),
        "model": "RNG-Miner-Pi",
        "wifi_state": "connected",
        "ip_address": "192.168.4.1",
        "ssid": f"RNG-Miner-{get_device_id()}",
        "mining_status": "ready",
        "system_info": system_info,
        "configuration_status": {
            "wifi_configured": True,
            "seed_phrase_set": False,
            "provider_id_set": False,
            "mining_ready": False
        },
        "timestamp": datetime.now().isoformat()
    }

    print(f"✅ Responding with device info")
    return jsonify(response)

@app.route('/device/configure', methods=['POST'])
def configure_device():
    """Device configuration endpoint"""
    print(f"📡 Configuration request from {request.remote_addr}")

    try:
        data = request.get_json()
        print(f"📝 Configuration data received: {list(data.keys()) if data else 'None'}")

        response = {
            "success": True,
            "message": "Configuration received successfully",
            "step_completed": "configuration",
            "next_step": "mining_ready",
            "timestamp": datetime.now().isoformat()
        }

        print(f"✅ Configuration successful")
        return jsonify(response)

    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Configuration failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - simple info page"""
    return jsonify({
        "device": "RNG-Miner",
        "device_id": get_device_id(),
        "status": "online",
        "endpoints": ["/health", "/device/info", "/device/configure"],
        "ip": "192.168.4.1"
    })

# Catch all other routes
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all for any other routes"""
    print(f"📡 Unknown route request: {path} from {request.remote_addr}")
    return jsonify({
        "error": "Route not found",
        "available_endpoints": ["/health", "/device/info", "/device/configure"],
        "requested_path": path
    }), 404

if __name__ == '__main__':
    print("🚀 Starting Simple RNG-Miner HTTP Server...")
    print("📡 Server will be accessible at:")
    print("   - http://192.168.4.1/health")
    print("   - http://192.168.4.1/device/info")
    print("   - http://192.168.4.1/device/configure")
    print("")

    try:
        # Run on port 80 (standard HTTP port)
        app.run(
            host='0.0.0.0',  # Bind to all interfaces
            port=80,
            debug=False,
            threaded=True
        )
    except PermissionError:
        print("❌ Permission denied for port 80. Trying port 8080...")
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            threaded=True
        )
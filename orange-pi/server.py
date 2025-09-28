#!/usr/bin/env python3
"""
RNG Miner HTTP Server

Enhanced HTTP server with comprehensive API endpoints.
Based on working patterns from old-bad-way implementation.
"""

import sys
import os

# Add the enhanced server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opt', 'device-software', 'src', 'http-server'))

# Import and use the enhanced server
from enhanced_server import EnhancedDeviceServer

def main():
    """Main entry point for the enhanced server"""
    print("🍊 Starting Enhanced RNG Miner HTTP Server...")
    print("📡 Server includes all API endpoints matching old-bad-way implementation")
    print("🔧 Configuration management and file persistence enabled")

    server = EnhancedDeviceServer()
    server.start_server()

if __name__ == '__main__':
    main()
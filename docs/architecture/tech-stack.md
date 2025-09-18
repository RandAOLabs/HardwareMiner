# Tech Stack

## Mobile Application
- **Framework:** React Native
- **Platforms:** iOS and Android (single codebase)
- **HTTP Client:** Built-in fetch or axios for REST API communication
- **Navigation:** React Navigation or similar framework
- **WiFi Capabilities:** WiFi scanning and network detection libraries
- **Certificate Handling:** Self-signed certificate trust for device IP ranges (192.168.x.x)

## Orange Pi Device Software
- **Operating System:** Armbian-compatible Linux distribution
- **Web Server:** Lightweight HTTP server (Node.js, Python Flask, or Go-based)
- **Protocol:** HTTPS REST API with TLS/self-signed certificates
- **Port:** Standard port 8080 for device communication
- **State Management:** Persistent state storage for WiFi state machine
- **Logging:** Request/response logging for debugging

## Container Platform
- **Docker:** Pre-installed container runtime
- **Docker Compose:** Pre-installed orchestration tool
- **Mining Software:** Containerized Randomness-Provider services
- **Auto-restart:** Docker restart policies for service reliability

## Networking
- **WiFi Hardware:** Orange Pi Zero 3 - 802.11ac dual-band (2.4GHz + 5GHz)
- **Bluetooth:** Bluetooth 5.0 (available but not used in V1)
- **Hotspot:** Orange Pi creates discoverable WiFi access point
- **DHCP:** Built-in DHCP server (192.168.12.0/24 range)
- **SSID Pattern:** "RNG-Miner-XXXXXXXX" (XXXXXXXX = 8-char hardware ID)
- **Security:** HTTPS/TLS communication, API rate limiting, input validation

## Mining Software Architecture
- **Repository:** https://github.com/RandAOLabs/Randomness-Provider.git
- **Installation Path:** /opt/mining/Randomness-Provider/
- **Working Directory:** /opt/mining/Randomness-Provider/docker-compose/
- **Startup Command:** `docker compose up -d`
- **Configuration:** .env file with SEED_PHRASE, WALLET_JSON, PROVIDER_ID
- **Logging Level:** LOG_CONSOLE_LEVEL=3 (operational logging)

## Development Tools
- **Version Control:** Git (repository pre-cloned on device)
- **Container Management:** Docker CLI and Docker Compose CLI
- **System Monitoring:** Standard Linux system utilities (htop-style metrics)
- **Network Testing:** Built-in network connectivity verification

## Security Stack
- **TLS/HTTPS:** Self-signed certificates for encrypted communication
- **Authentication:** User-set device passwords (replaces hardcoded credentials)
- **Rate Limiting:** 30 requests/minute, 100/hour burst protection
- **Input Validation:** Comprehensive sanitization of all user inputs
- **Upgrade Path:** V1.1 dynamic tokens, V1.2 certificate-based auth, V2.0 enterprise security
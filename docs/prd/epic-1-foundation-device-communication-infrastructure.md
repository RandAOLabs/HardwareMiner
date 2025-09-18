# Epic 1: Foundation & Device Communication Infrastructure

**Epic Goal:** Establish the foundational infrastructure for Orange Pi device software and React Native mobile app with basic device discovery and communication capabilities. This epic delivers a working proof-of-concept where the mobile app can discover, connect to, and exchange basic data with Orange Pi devices, validating the core technical architecture.

## Story 1.1: Orange Pi HTTP Server Setup
As a **system administrator**,
I want **a lightweight HTTP server running on the Orange Pi device**,
so that **the mobile app can communicate with the device via REST API endpoints**.

### Acceptance Criteria
1. HTTP server starts automatically on Orange Pi boot
2. Server listens on a standard port (e.g., 8080) accessible via WiFi
3. Server responds to basic health check endpoint (GET /health)
4. Server logs incoming requests for debugging
5. Server handles graceful shutdown and restart

## Story 1.2: Orange Pi WiFi Hotspot Creation
As a **user with a new Orange Pi device**,
I want **the device to automatically create a discoverable WiFi hotspot**,
so that **my mobile app can find and connect to the device for initial setup**.

### Acceptance Criteria
1. Orange Pi creates WiFi hotspot on startup with SSID pattern "RNG-Miner-XXXXXXXX" (XXXXXXXX is unique 8-character hardware-based device ID)
2. Hotspot uses hardcoded password: "RNG-Miner-Password-123"
3. Hotspot provides DHCP service for connecting devices (192.168.12.0/24 range)
4. HTTP server is accessible via hotspot connection
5. Hotspot remains active until device successfully connects to home WiFi

## Story 1.3: React Native App Foundation
As a **developer**,
I want **a React Native app project with basic navigation and network capabilities**,
so that **we have a foundation for building the device setup interface**.

### Acceptance Criteria
1. React Native project builds successfully for both iOS and Android
2. App includes basic navigation framework (React Navigation or similar)
3. App includes HTTP client library for API communication
4. App includes WiFi scanning/detection capabilities
5. App runs on physical devices (not just simulator)

## Story 1.4: Device Discovery Implementation
As a **mobile app user**,
I want **the app to automatically discover available Orange Pi devices**,
so that **I can select which device to configure**.

### Acceptance Criteria
1. App scans for devices with Orange Pi hotspot SSID pattern "RNG-Miner-XXXXXXXX"
2. App displays list of discovered devices with signal strength
3. App can connect to selected Orange Pi hotspot using hardcoded password
4. App verifies HTTP server accessibility after connection
5. App handles cases where no devices are found

## Story 1.5: Basic Device Communication Test
As a **mobile app user**,
I want **the app to successfully communicate with the Orange Pi device**,
so that **I can verify the connection is working before proceeding with setup**.

### Acceptance Criteria
1. App sends test request to Orange Pi HTTPS server with authentication
2. Orange Pi responds with device information (model, status, device ID, etc.)
3. App displays successful connection confirmation to user
4. App handles communication failures with clear error messages
5. Communication works reliably across both 2.4GHz and 5GHz bands

## Story 1.6: WiFi State Machine Implementation
As a **Orange Pi device**,
I want **a robust state machine managing WiFi connectivity and mode transitions**,
so that **I can reliably switch between setup mode and operational mode with automatic error recovery**.

### Acceptance Criteria
1. Device implements comprehensive state machine with defined states: BOOT, SETUP_MODE, HOTSPOT_STARTING, HOTSPOT_ACTIVE, CREDENTIALS_RECEIVED, HOTSPOT_TEARDOWN, CONNECTING, CONNECT_RETRY, CONNECTED, NETWORK_VALIDATION, OPERATIONAL, MINING_READY, WIFI_FAILED, ERROR_RECOVERY
2. State transitions respect timing constraints: 30s hotspot teardown, 20s connection timeout, 10s retry delay
3. Device automatically falls back to setup mode after 3 failed WiFi connection attempts
4. State machine persists current state to survive crashes and reboots
5. Device provides real-time state information via API endpoints for mobile app monitoring
6. Comprehensive error recovery with manual reset capability for critical failures

## Story 1.7: Enhanced Security Foundation
As a **system administrator**,
I want **basic security measures implemented for device communication**,
so that **we have a foundation for future security enhancements**.

### Acceptance Criteria
1. All API communication uses HTTPS/TLS with self-signed certificates
2. Mobile app trusts self-signed certificates from device IP ranges (192.168.x.x)
3. API endpoints implement rate limiting (30 req/min, 100/hour burst)
4. All user inputs (WiFi credentials, seed phrases, scripts) undergo validation and sanitization
5. System prompts user to set custom device password during initial setup
6. Clear upgrade path documented for V1.1 security enhancements (dynamic tokens, encryption)

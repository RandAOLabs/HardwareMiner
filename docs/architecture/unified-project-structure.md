# Unified Project Structure

## Multi-Repository Architecture

This project uses a **multi-repository structure** with separate codebases for each platform:

### Repository Organization
- **Mobile App Repository:** React Native codebase for iOS/Android
- **Orange Pi Software Repository:** Device-side setup and communication software

## Orange Pi Device File Structure

```
/opt/
├── mining/
│   └── Randomness-Provider/           # Pre-cloned mining software repository
│       ├── docker-compose/            # Working directory for Docker operations
│       │   ├── .env                  # Configuration file (created during setup)
│       │   ├── docker-compose.yml    # Container orchestration configuration
│       │   └── ...                   # Additional compose-related files
│       └── ...                       # Other repository contents
├── device-software/                   # Orange Pi setup and communication software
│   ├── src/
│   │   ├── http-server/              # HTTP server implementation
│   │   ├── wifi-manager/             # WiFi state machine and hotspot management
│   │   ├── device-info/              # Hardware ID generation and device status
│   │   └── config-manager/           # Configuration file management (.env creation)
│   ├── scripts/
│   │   ├── startup.sh               # Boot-time initialization script
│   │   ├── wifi-state-machine.sh    # WiFi state management
│   │   └── docker-manager.sh        # Docker container lifecycle management
│   ├── config/
│   │   ├── device-config.json       # Device-specific configuration
│   │   └── wifi-state.json          # Persistent WiFi state storage
│   └── logs/
│       ├── device.log               # General device operation logs
│       ├── http-server.log          # HTTP server request/response logs
│       └── wifi-manager.log         # WiFi state machine logs
```

## Mobile App Project Structure (React Native)

```
mobile-app/
├── src/
│   ├── screens/
│   │   ├── DeviceDiscovery/         # WiFi scanning and device selection
│   │   ├── DeviceSetup/             # Configuration input screens
│   │   ├── SetupProgress/           # Status monitoring during setup
│   │   └── DeviceManagement/       # Ongoing device communication
│   ├── services/
│   │   ├── wifi-scanner/            # WiFi network detection
│   │   ├── device-api/              # HTTP client for device communication
│   │   ├── certificate-manager/     # Self-signed certificate handling
│   │   └── crypto-utils/            # RSA key generation and validation
│   ├── components/
│   │   ├── common/                  # Shared UI components
│   │   ├── forms/                   # Input forms for setup data
│   │   └── status/                  # Status indicators and progress displays
│   ├── navigation/
│   │   └── AppNavigator.js          # React Navigation configuration
│   ├── utils/
│   │   ├── validation/              # Input validation utilities
│   │   └── constants/               # Application constants and configurations
│   └── hooks/
│       ├── useDeviceDiscovery/      # Device scanning and connection logic
│       ├── useDeviceSetup/          # Setup process orchestration
│       └── useDeviceStatus/         # Real-time status monitoring
├── android/                         # Android-specific configuration
├── ios/                            # iOS-specific configuration
└── __tests__/                      # Unit and integration tests
```

## Configuration File Locations

### Orange Pi Device Configuration
- **Device Config:** `/opt/device-software/config/device-config.json`
- **WiFi State:** `/opt/device-software/config/wifi-state.json`
- **Mining Config:** `/opt/mining/Randomness-Provider/docker-compose/.env`
- **Service Logs:** `/opt/device-software/logs/`

### Mobile App Configuration
- **Environment Config:** `mobile-app/.env` (development)
- **Build Configs:** `mobile-app/android/app/build.gradle`, `mobile-app/ios/Info.plist`

## API Endpoint Structure

### Device HTTP Server Endpoints
```
GET  /health                         # Health check endpoint
GET  /device/info                    # Device information and status
GET  /device/state                   # Current WiFi state machine status
POST /setup/wifi                     # WiFi credentials configuration
POST /setup/mining                   # Mining configuration and .env creation
POST /setup/password                 # Device password configuration
GET  /setup/progress                 # Setup progress status
POST /device/reset                   # Manual device reset (with confirmation)
```

## File Naming Conventions

### Orange Pi Device Files
- **Scripts:** kebab-case with `.sh` extension (e.g., `wifi-state-machine.sh`)
- **Config Files:** kebab-case with appropriate extension (e.g., `device-config.json`)
- **Log Files:** kebab-case with `.log` extension (e.g., `http-server.log`)
- **Source Code:** Follow language conventions (Python: snake_case, JavaScript: camelCase)

### Mobile App Files
- **React Components:** PascalCase (e.g., `DeviceDiscovery.jsx`)
- **Services/Utils:** camelCase (e.g., `deviceApiService.js`)
- **Config Files:** kebab-case (e.g., `api-config.js`)
- **Test Files:** Component name + `.test.js` (e.g., `DeviceDiscovery.test.js`)

## Deployment Structure

### Orange Pi Device Deployment
- Software pre-installed at `/opt/device-software/`
- Mining repository pre-cloned at `/opt/mining/Randomness-Provider/`
- Docker images pre-pulled during device preparation
- Startup scripts configured for automatic boot execution

### Mobile App Deployment
- Standard React Native build process for iOS/Android app stores
- Development builds for testing with physical devices
- Configuration for connecting to device IP ranges (192.168.x.x)
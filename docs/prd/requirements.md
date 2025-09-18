# Requirements

## Functional Requirements

**FR1:** The mobile app must discover Orange Pi devices in setup mode via WiFi scanning and lock to specific device based on 8-character hardware identifier
**FR2:** The app must establish secure communication with Orange Pi devices using HTTPS/TLS with self-signed certificates
**FR3:** The app must capture user's home WiFi network credentials (SSID + password)
**FR4:** The app must capture and transfer the 12-word seed phrase to Orange Pi device
**FR5:** The app must collect and transfer various mining configuration parameters to Orange Pi device
**FR6:** The Orange Pi setup software must receive WiFi credentials, 12 words, and mining configs from mobile app
**FR7:** The Orange Pi must connect to the specified home WiFi network using received credentials
**FR8:** The Orange Pi must continue communication with mobile app after connecting to home WiFi
**FR9:** The mining software must be pre-packaged on Orange Pi device (git repo + images bundled during device preparation)
**FR10:** The Orange Pi must initialize mining software with received 12-word seed phrase and configurations
**FR11:** The mobile app must display simple setup progress and confirmation of successful connection
**FR12:** The system must provide manual device wipe functionality with user confirmation (not automatic on failures)
**FR13:** The Orange Pi must create a discoverable WiFi hotspot during initial setup phase
**FR14:** The setup software must work on any Armbian-compatible OS flavor
**FR15:** The mobile app must support ongoing communication and updates with configured devices
**FR16:** The Orange Pi must have the Randomness-Provider repository pre-cloned at /opt/mining/Randomness-Provider/ during device preparation with Docker images pre-pulled
**FR17:** The Orange Pi setup software must create a properly formatted .env file in the docker-compose directory
**FR18:** The Orange Pi must populate .env file with received 12-word seed phrase in SEED_PHRASE field
**FR19:** The Orange Pi must populate .env file with WALLET_JSON, PROVIDER_ID, and LOG_CONSOLE_LEVEL fields
**FR20:** The Orange Pi must execute 'docker compose up -d' to start mining services after .env file creation
**FR21:** The Orange Pi must ensure Docker Compose services restart automatically on failure and system reboot
**FR22:** The Orange Pi must implement robust WiFi state machine with automatic fallback to setup mode on connection failures
**FR23:** The mobile app must prompt user to set custom device password during initial setup for enhanced security
**FR24:** The system must implement comprehensive input validation and sanitization for all user inputs
**FR25:** The Orange Pi must implement API rate limiting (30 requests/minute, 100/hour burst) to prevent abuse
**FR26:** The mobile app must handle all device state transitions and error codes with appropriate user guidance
**FR27:** The Orange Pi must generate unique 8-character device identifier based on hardware identifiers for consistent device recognition

## Non-Functional Requirements

**NFR1:** Setup process prioritizes reliability over speed - "something working" is the primary goal
**NFR2:** V1 communication uses HTTPS/TLS with self-signed certificates as foundation for security upgrade path
**NFR3:** The mobile app must work on both iOS and Android platforms
**NFR4:** Orange Pi devices must operate solely through WiFi connectivity
**NFR5:** Mining software pre-packaging eliminates download/install time during setup
**NFR6:** User setup process must be extremely simple with minimal input requirements
**NFR7:** The system must handle WiFi network failures with automatic retry and graceful fallback within 60-second transition window
**NFR8:** Orange Pi setup software must have minimal resource requirements
**NFR9:** WiFi state transitions must be resilient with comprehensive error recovery and user feedback
**NFR10:** Security implementation must provide clear upgrade path from V1 basic security to enterprise-grade authentication

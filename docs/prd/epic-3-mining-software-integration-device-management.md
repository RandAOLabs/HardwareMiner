# Epic 3: Mining Software Integration & Device Management

**Epic Goal:** Integrate Docker-based mining software with 12-word cryptocurrency wallet seed phrase handling and implement comprehensive device monitoring and management capabilities. This epic transforms the configured Orange Pi devices into fully functional mining nodes with ongoing communication and management through the mobile app.

## Story 3.1: 12-Word Seed Phrase Input Interface
As a **mobile app user**,
I want **a secure interface to enter my 12-word cryptocurrency wallet seed phrase**,
so that **the Orange Pi device can initialize mining operations with my wallet**.

### Acceptance Criteria
1. App provides 12 individual input fields for seed phrase words
2. App validates each word against standard BIP39 word list
3. App provides auto-complete suggestions for valid BIP39 words
4. App validates complete 12-word phrase for proper checksum
5. App securely handles seed phrase data without logging or persistence

## Story 3.2: Mining Configuration Parameters Input
As a **mobile app user**,
I want **to configure my Provider ID and wallet parameters**,
so that **the Orange Pi device can create a complete .env configuration**.

### Acceptance Criteria
1. App provides input field for PROVIDER_ID (or generates one automatically)
2. App generates WALLET_JSON RSA key components automatically
3. App sets LOG_CONSOLE_LEVEL to default value of 3
4. App validates all required .env parameters are collected
5. App allows user to review complete configuration before sending

## Story 3.3: Configuration Data Transfer to Device
As a **mobile app user**,
I want **to send my seed phrase and mining configuration to the Orange Pi**,
so that **the device can initialize mining operations**.

### Acceptance Criteria
1. App sends 12-word seed phrase securely to Orange Pi device
2. App transfers all mining configuration parameters to device
3. Orange Pi validates received seed phrase format and checksum
4. Orange Pi confirms successful receipt of all configuration data
5. Orange Pi stores configuration securely for mining initialization

## Story 3.4: Docker Mining Software Initialization
As a **Orange Pi device**,
I want **to create the .env file and start the Randomness-Provider mining software**,
so that **I can begin mining operations using Docker Compose**.

### Acceptance Criteria
1. Orange Pi creates .env file in /opt/mining/Randomness-Provider/docker-compose/ directory
2. Orange Pi populates SEED_PHRASE field with received 12-word phrase
3. Orange Pi populates WALLET_JSON, PROVIDER_ID, and LOG_CONSOLE_LEVEL fields
4. Orange Pi executes `docker compose up -d` from docker-compose directory
5. Orange Pi verifies Docker containers are running and reports status to mobile app
6. Orange Pi ensures Docker Compose services restart on failure and system reboot

## Story 3.5: Device Status Monitoring System
As a **mobile app user**,
I want **to monitor the operational status of my Orange Pi device**,
so that **I can verify mining operations and system health**.

### Acceptance Criteria
1. App displays WiFi connection status (connected/disconnected)
2. App shows system metrics (CPU, memory, disk usage similar to htop)
3. App reports Docker container status (running/stopped/error)
4. App indicates mining software operational status
5. App refreshes status information automatically at regular intervals

## Story 3.6: Device Update Script Execution
As a **mobile app user**,
I want **to send update scripts to my Orange Pi device**,
so that **I can perform maintenance and updates remotely**.

### Acceptance Criteria
1. App provides interface to send update.sh scripts to Orange Pi
2. Orange Pi receives and validates update script format
3. Orange Pi executes update scripts with root permissions
4. Orange Pi reports script execution progress and results
5. Orange Pi handles script execution timeouts and error conditions

# Epic 2: Complete Setup Flow & WiFi Configuration

**Epic Goal:** Implement the complete device setup workflow that allows users to configure Orange Pi devices with WiFi credentials and basic settings. This epic delivers a working end-to-end setup process where users can take a fresh Orange Pi device and get it connected to their home network with all necessary configuration data transferred.

## Story 2.1: WiFi Network Scanning in Mobile App
As a **mobile app user**,
I want **the app to scan and display available WiFi networks**,
so that **I can easily select my home network without typing the SSID manually**.

### Acceptance Criteria
1. App scans for available WiFi networks in the area
2. App displays networks with SSID names and signal strength
3. App filters out hidden networks or provides option to add custom SSID
4. App allows user to select their desired home network
5. App handles cases where target network requires manual SSID entry

## Story 2.2: WiFi Credentials Input Interface
As a **mobile app user**,
I want **a simple interface to enter my WiFi password**,
so that **I can provide network credentials for the Orange Pi device**.

### Acceptance Criteria
1. App presents secure password input field for selected WiFi network
2. App shows/hides password toggle for user convenience
3. App validates password meets minimum requirements (non-empty)
4. App provides clear indication of which network is being configured
5. App allows user to go back and select different network if needed

## Story 2.3: WiFi Credentials Transfer to Device
As a **mobile app user**,
I want **the app to securely send WiFi credentials to the Orange Pi**,
so that **the device can connect to my home network**.

### Acceptance Criteria
1. App sends WiFi SSID and password to Orange Pi via HTTP POST
2. Orange Pi receives and validates credential format
3. Orange Pi confirms receipt of credentials to mobile app
4. Orange Pi stores credentials securely for connection attempt
5. Communication uses hardcoded authentication ("RNG-Miner-Password-123")

## Story 2.4: Orange Pi WiFi Connection Implementation
As a **Orange Pi device**,
I want **to connect to the home WiFi network using received credentials**,
so that **I can provide internet connectivity for ongoing operations**.

### Acceptance Criteria
1. Orange Pi attempts connection to specified WiFi network
2. Orange Pi validates successful network connection and internet access
3. Orange Pi maintains HTTP server accessibility on new network
4. Orange Pi reports connection status back to mobile app
5. Orange Pi falls back to hotspot mode if connection fails

## Story 2.5: Setup Progress Monitoring
As a **mobile app user**,
I want **real-time updates on the setup progress**,
so that **I know the device is successfully connecting and configuring**.

### Acceptance Criteria
1. App displays current setup step (connecting, validating, etc.)
2. App polls Orange Pi for status updates during setup process
3. App shows success confirmation when WiFi connection established
4. App provides clear error messages if setup fails at any step
5. App offers option to restart setup process on failure

## Story 2.6: Setup Completion and Network Transition
As a **mobile app user**,
I want **the app to reconnect to the Orange Pi on the home network**,
so that **I can continue communicating with the device after setup**.

### Acceptance Criteria
1. App detects when Orange Pi has connected to home WiFi (scans for "RNG-Miner-XXXXXXXX" hostname pattern)
2. App automatically reconnects to Orange Pi on home network using same device ID
3. App verifies continued communication with configured device
4. App confirms setup completion and device operational status
5. App handles network transition smoothly without user intervention

# Coding Standards

## General Principles

### Code Quality
- **Reliability Over Speed:** Prioritize working, robust solutions over performance optimization
- **Clear Error Handling:** All error conditions must be handled with clear user feedback
- **Comprehensive Logging:** Log all significant operations for debugging and monitoring
- **Input Validation:** Validate and sanitize all user inputs and API parameters
- **Security First:** Implement security measures even in V1 for upgrade path foundation

### Documentation
- **Code Comments:** Document complex logic and state machine transitions
- **API Documentation:** Document all endpoints with request/response formats
- **Configuration Documentation:** Document all configuration options and environment variables
- **Error Codes:** Document all error codes and their meanings for user guidance

## Orange Pi Device Software Standards

### Language-Specific Standards

#### Python (Recommended for HTTP Server)
```python
# File naming: snake_case
# Class naming: PascalCase
# Function naming: snake_case
# Constants: UPPER_SNAKE_CASE

# Example structure:
class WiFiStateManager:
    def __init__(self):
        self.current_state = WiFiState.BOOT
        self.transition_timeout = 30

    def transition_to_state(self, new_state: WiFiState) -> bool:
        """Transition to new WiFi state with validation."""
        if self._is_valid_transition(new_state):
            self._log_state_transition(self.current_state, new_state)
            self.current_state = new_state
            return True
        return False
```

#### Bash Scripts
```bash
#!/bin/bash
# File naming: kebab-case.sh
# Function naming: snake_case
# Variables: UPPER_SNAKE_CASE for globals, lower_snake_case for locals

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Example structure:
LOG_FILE="/opt/device-software/logs/startup.log"

function log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE"
}

function start_http_server() {
    log_message "Starting HTTP server on port 8080"
    # Implementation here
}
```

### Error Handling Standards

#### HTTP Server Error Responses
```json
{
    "success": false,
    "error_code": "WIFI_CONNECTION_FAILED",
    "message": "Unable to connect to WiFi network",
    "details": {
        "ssid": "provided_network_name",
        "attempt": 3,
        "max_attempts": 3
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### State Machine Error Handling
- All state transitions must validate before executing
- Failed transitions must log error details and maintain current state
- Critical failures must trigger ERROR_RECOVERY state with manual intervention capability

### Configuration Management

#### Environment Variables
```bash
# .env file format (mining configuration)
LOG_CONSOLE_LEVEL=3
SEED_PHRASE="word1 word2 word3 ... word12"
WALLET_JSON='{"kty":"RSA","e":"...","n":"...","d":"...","p":"...","q":"...","dp":"...","dq":"...","qi":"..."}'
PROVIDER_ID='unique_provider_identifier'
```

#### Device Configuration (JSON)
```json
{
    "device_id": "A1B2C3D4",
    "hotspot_ssid": "RNG-Miner-A1B2C3D4",
    "hotspot_password": "RNG-Miner-Password-123",
    "http_port": 8080,
    "dhcp_range": "192.168.12.0/24",
    "wifi_state_timeout": 30,
    "connection_retry_limit": 3,
    "api_rate_limit": {
        "requests_per_minute": 30,
        "burst_limit": 100
    }
}
```

## Mobile App Standards (React Native)

### Component Structure
```jsx
// File naming: PascalCase.jsx
// Component naming: PascalCase
// Props interface: ComponentNameProps
// Hooks: use + descriptive name

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface DeviceDiscoveryProps {
    onDeviceSelected: (deviceId: string) => void;
    scanningEnabled: boolean;
}

export const DeviceDiscovery: React.FC<DeviceDiscoveryProps> = ({
    onDeviceSelected,
    scanningEnabled
}) => {
    const [discoveredDevices, setDiscoveredDevices] = useState([]);
    const [scanError, setScanError] = useState(null);

    useEffect(() => {
        if (scanningEnabled) {
            startDeviceScan();
        }
    }, [scanningEnabled]);

    const startDeviceScan = async () => {
        try {
            // Implementation
        } catch (error) {
            setScanError(error.message);
        }
    };

    return (
        <View style={styles.container}>
            {/* Component JSX */}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 16,
    },
});
```

### API Service Standards
```javascript
// File naming: camelCase.js
// Service class naming: PascalCase + Service
// Methods: camelCase

class DeviceApiService {
    constructor(baseUrl = 'https://192.168.12.1:8080') {
        this.baseUrl = baseUrl;
        this.timeout = 10000; // 10 second timeout
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            // Log error details for debugging
            console.error(`API Request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async getDeviceInfo() {
        return this.makeRequest('/device/info');
    }

    async setupWifi(credentials) {
        return this.makeRequest('/setup/wifi', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
    }
}
```

### Input Validation Standards

#### WiFi Credentials Validation
```javascript
const validateWifiCredentials = (ssid, password) => {
    const errors = {};

    if (!ssid || ssid.trim().length === 0) {
        errors.ssid = 'Network name is required';
    } else if (ssid.length > 32) {
        errors.ssid = 'Network name must be 32 characters or less';
    }

    if (!password) {
        errors.password = 'Password is required';
    } else if (password.length < 8) {
        errors.password = 'Password must be at least 8 characters';
    }

    return {
        isValid: Object.keys(errors).length === 0,
        errors
    };
};
```

#### Seed Phrase Validation
```javascript
const validateSeedPhrase = (seedPhrase) => {
    if (!seedPhrase || typeof seedPhrase !== 'string') {
        return { isValid: false, error: 'Seed phrase is required' };
    }

    const words = seedPhrase.trim().split(/\s+/);

    if (words.length !== 12) {
        return { isValid: false, error: 'Seed phrase must contain exactly 12 words' };
    }

    // Additional validation for word dictionary if needed
    return { isValid: true };
};
```

## Testing Standards

### Unit Test Structure
```javascript
// File naming: ComponentName.test.js
// Test descriptions: descriptive, behavior-focused

describe('DeviceApiService', () => {
    let apiService;

    beforeEach(() => {
        apiService = new DeviceApiService();
    });

    describe('getDeviceInfo', () => {
        it('should return device information when request succeeds', async () => {
            // Test implementation
        });

        it('should throw error when device is unreachable', async () => {
            // Test implementation
        });
    });
});
```

### Integration Test Requirements
- Test complete WiFi setup flow from app to device
- Validate state machine transitions work correctly
- Verify error handling provides appropriate user feedback
- Test network failure scenarios and recovery

## Security Standards

### Input Sanitization
- Sanitize all user inputs before processing
- Validate data types and formats
- Prevent injection attacks in configuration files
- Rate limit API endpoints (30 req/min, 100/hour burst)

### Certificate Handling
- Generate self-signed certificates on device startup
- Mobile app must trust certificates from 192.168.x.x IP ranges
- Log certificate validation attempts for debugging

### Password Security
- User-set device passwords replace hardcoded credentials
- Minimum password requirements: 8 characters
- Store password hashes, not plain text (implementation specific)

### Upgrade Path Preparation
- Code structure must support future security enhancements
- V1.1: Dynamic device tokens
- V1.2: Certificate-based authentication
- V2.0: Enterprise security features
# Testing Strategy

## Testing Philosophy

### Priority: Reliability Over Speed
- Focus on testing critical paths and error scenarios
- Ensure robust error handling and recovery mechanisms
- Validate state machine transitions and edge cases
- Test network failure scenarios and fallback mechanisms

### Testing Pyramid Approach
1. **Unit Tests** - Individual component and function validation
2. **Integration Tests** - App-to-device communication workflows
3. **End-to-End Tests** - Complete setup flow validation
4. **Device Testing** - Physical hardware validation

## Orange Pi Device Software Testing

### Unit Testing Requirements

#### HTTP Server Testing
```python
# Example test structure for Python HTTP server
import unittest
from unittest.mock import patch, Mock
from http_server import DeviceHttpServer, WiFiStateManager

class TestDeviceHttpServer(unittest.TestCase):

    def setUp(self):
        self.server = DeviceHttpServer()
        self.wifi_manager = Mock(spec=WiFiStateManager)

    def test_health_endpoint_returns_success(self):
        """Test that /health endpoint returns successful response"""
        response = self.server.handle_health_check()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'healthy')

    def test_wifi_setup_validates_credentials(self):
        """Test that WiFi setup validates credentials format"""
        invalid_credentials = {"ssid": "", "password": "short"}
        response = self.server.handle_wifi_setup(invalid_credentials)
        self.assertEqual(response.status_code, 400)
        self.assertIn('validation_errors', response.json)

    @patch('wifi_manager.connect_to_network')
    def test_wifi_setup_handles_connection_failure(self, mock_connect):
        """Test WiFi setup handles connection failures gracefully"""
        mock_connect.return_value = False
        credentials = {"ssid": "TestNetwork", "password": "validpassword"}
        response = self.server.handle_wifi_setup(credentials)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error_code'], 'WIFI_CONNECTION_FAILED')
```

#### WiFi State Machine Testing
```python
class TestWiFiStateMachine(unittest.TestCase):

    def setUp(self):
        self.state_machine = WiFiStateManager()

    def test_state_transitions_follow_valid_paths(self):
        """Test that state transitions follow defined valid paths"""
        # Test valid transition
        self.assertTrue(self.state_machine.transition_to_state(WiFiState.SETUP_MODE))
        self.assertEqual(self.state_machine.current_state, WiFiState.SETUP_MODE)

        # Test invalid transition
        self.assertFalse(self.state_machine.transition_to_state(WiFiState.MINING_READY))
        self.assertEqual(self.state_machine.current_state, WiFiState.SETUP_MODE)

    def test_state_persistence_survives_reboot(self):
        """Test that state machine persists state across reboots"""
        self.state_machine.transition_to_state(WiFiState.CONNECTED)
        self.state_machine.save_state()

        # Simulate reboot
        new_state_machine = WiFiStateManager()
        new_state_machine.load_state()
        self.assertEqual(new_state_machine.current_state, WiFiState.CONNECTED)

    def test_error_recovery_from_failed_states(self):
        """Test that error recovery works from failed states"""
        self.state_machine.current_state = WiFiState.WIFI_FAILED
        self.state_machine.handle_error_recovery()
        self.assertEqual(self.state_machine.current_state, WiFiState.SETUP_MODE)
```

#### Configuration Management Testing
```bash
#!/bin/bash
# Example bash test script for configuration management

test_env_file_creation() {
    local test_seed="word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12"
    local test_wallet='{"kty":"RSA","e":"test","n":"test"}'
    local test_provider_id="TEST_PROVIDER_123"

    # Test .env file creation
    create_env_file "$test_seed" "$test_wallet" "$test_provider_id"

    # Verify file exists and contains correct content
    assert_file_exists "/opt/mining/Randomness-Provider/docker-compose/.env"
    assert_file_contains "/opt/mining/Randomness-Provider/docker-compose/.env" "SEED_PHRASE=\"$test_seed\""
    assert_file_contains "/opt/mining/Randomness-Provider/docker-compose/.env" "LOG_CONSOLE_LEVEL=3"

    echo "✓ Environment file creation test passed"
}

test_docker_compose_startup() {
    # Test Docker Compose startup
    cd /opt/mining/Randomness-Provider/docker-compose/

    # Mock docker compose command for testing
    DOCKER_COMPOSE_CMD="echo docker compose up -d"

    result=$(start_mining_services)
    assert_equals "$result" "docker compose up -d"

    echo "✓ Docker Compose startup test passed"
}
```

### Integration Testing Requirements

#### App-to-Device Communication Testing
```javascript
// Example integration test for mobile app
describe('Device Communication Integration', () => {
    let deviceApiService;
    let mockDevice;

    beforeAll(async () => {
        // Start mock device server for testing
        mockDevice = new MockDeviceServer();
        await mockDevice.start();
        deviceApiService = new DeviceApiService('https://localhost:8080');
    });

    afterAll(async () => {
        await mockDevice.stop();
    });

    describe('Device Discovery Flow', () => {
        it('should discover mock device with correct SSID pattern', async () => {
            const devices = await deviceApiService.scanForDevices();
            expect(devices).toHaveLength(1);
            expect(devices[0].ssid).toMatch(/^RNG-Miner-[A-Z0-9]{8}$/);
        });

        it('should connect to discovered device successfully', async () => {
            const devices = await deviceApiService.scanForDevices();
            const connectionResult = await deviceApiService.connectToDevice(devices[0]);
            expect(connectionResult.success).toBe(true);
        });
    });

    describe('WiFi Setup Flow', () => {
        it('should send WiFi credentials and receive confirmation', async () => {
            const credentials = { ssid: 'TestNetwork', password: 'testpassword123' };
            const result = await deviceApiService.setupWifi(credentials);

            expect(result.success).toBe(true);
            expect(result.message).toContain('WiFi configuration received');
        });

        it('should handle invalid WiFi credentials gracefully', async () => {
            const invalidCredentials = { ssid: '', password: 'short' };

            await expect(deviceApiService.setupWifi(invalidCredentials))
                .rejects.toThrow('validation_errors');
        });
    });

    describe('Mining Setup Flow', () => {
        it('should configure mining software with valid parameters', async () => {
            const miningConfig = {
                seedPhrase: 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
                walletJson: '{"kty":"RSA","e":"AQAB","n":"test"}',
                providerId: 'TEST_PROVIDER_123'
            };

            const result = await deviceApiService.setupMining(miningConfig);
            expect(result.success).toBe(true);
            expect(result.mining_status).toBe('configured');
        });
    });
});
```

### End-to-End Testing Strategy

#### Complete Setup Flow Testing
1. **Device Preparation Testing**
   - Verify device creates hotspot on startup
   - Confirm HTTP server starts and responds to health checks
   - Test device ID generation and SSID creation

2. **Mobile App Flow Testing**
   - Test device discovery and selection
   - Validate WiFi credential input and validation
   - Verify seed phrase input and formatting
   - Test progress monitoring and status updates

3. **Device Configuration Testing**
   - Test WiFi connection with provided credentials
   - Verify .env file creation with correct format
   - Test Docker Compose startup and container health
   - Validate state machine transitions throughout process

4. **Error Scenario Testing**
   - Test network connection failures and retries
   - Validate error recovery and fallback to setup mode
   - Test invalid input handling and user feedback
   - Verify timeout handling and graceful degradation

### Physical Hardware Testing

#### Orange Pi Device Testing
```bash
#!/bin/bash
# Physical hardware test script

run_hardware_tests() {
    echo "Running Orange Pi hardware tests..."

    # Test WiFi hardware functionality
    test_wifi_hardware

    # Test hotspot creation capability
    test_hotspot_creation

    # Test Docker functionality
    test_docker_functionality

    # Test system resource availability
    test_system_resources

    echo "Hardware tests completed"
}

test_wifi_hardware() {
    echo "Testing WiFi hardware..."

    # Check WiFi interface exists
    if ! iwconfig wlan0 >/dev/null 2>&1; then
        echo "❌ WiFi interface wlan0 not found"
        return 1
    fi

    # Test WiFi scanning capability
    if ! iwlist wlan0 scan >/dev/null 2>&1; then
        echo "❌ WiFi scanning failed"
        return 1
    fi

    echo "✓ WiFi hardware test passed"
}

test_hotspot_creation() {
    echo "Testing hotspot creation..."

    # Test hostapd configuration
    if ! which hostapd >/dev/null 2>&1; then
        echo "❌ hostapd not installed"
        return 1
    fi

    # Test DHCP server capability
    if ! which dnsmasq >/dev/null 2>&1; then
        echo "❌ dnsmasq not installed"
        return 1
    fi

    echo "✓ Hotspot creation test passed"
}
```

#### Mobile App Device Testing
- Test on actual iOS and Android devices (not just simulators)
- Validate WiFi scanning works on different device models
- Test certificate handling with actual self-signed certificates
- Verify app performance with real network conditions and latency

### Test Data Management

#### Mock Device Responses
```json
{
    "health_check_response": {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "device_id": "A1B2C3D4",
        "uptime": 3600
    },
    "device_info_response": {
        "device_id": "A1B2C3D4",
        "model": "Orange Pi Zero 3",
        "wifi_state": "HOTSPOT_ACTIVE",
        "ip_address": "192.168.12.1",
        "ssid": "RNG-Miner-A1B2C3D4",
        "mining_status": "not_configured"
    },
    "wifi_setup_success": {
        "success": true,
        "message": "WiFi configuration received",
        "next_state": "CONNECTING"
    },
    "wifi_setup_error": {
        "success": false,
        "error_code": "VALIDATION_ERROR",
        "validation_errors": {
            "ssid": "SSID cannot be empty",
            "password": "Password must be at least 8 characters"
        }
    }
}
```

#### Test Environment Configuration
```javascript
// Test configuration for different environments
const testConfig = {
    development: {
        mockDeviceUrl: 'https://localhost:8080',
        enableCertificateValidation: false,
        logLevel: 'debug'
    },
    staging: {
        mockDeviceUrl: 'https://test-device.local:8080',
        enableCertificateValidation: true,
        logLevel: 'info'
    },
    production: {
        // Production testing with real devices
        enableCertificateValidation: true,
        logLevel: 'error'
    }
};
```

## Continuous Testing Strategy

### Automated Test Execution
- Unit tests run on every code commit
- Integration tests run on pull request creation
- End-to-end tests run nightly with mock devices
- Hardware tests run weekly with physical devices

### Test Coverage Requirements
- **Minimum Unit Test Coverage:** 80% for critical paths
- **Integration Test Coverage:** All API endpoints and state transitions
- **Error Scenario Coverage:** All defined error codes and recovery paths
- **Hardware Test Coverage:** All physical hardware capabilities

### Test Reporting
- Generate test reports with pass/fail status
- Track test execution time and performance
- Document failing tests with reproduction steps
- Maintain test result history for regression analysis
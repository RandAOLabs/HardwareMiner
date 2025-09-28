#!/bin/bash
# Orange Pi WiFi Hotspot Integration Test Script
# Test complete hotspot functionality including HTTP server integration

set -euo pipefail

# Configuration
DEVICE_SOFTWARE_PATH="/opt/device-software"
LOG_FILE="$DEVICE_SOFTWARE_PATH/logs/integration-test.log"

# Test configuration
TEST_TIMEOUT=30
HOTSPOT_IP="192.168.12.1"
HTTP_PORT="8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test result functions
test_start() {
    local test_name="$1"
    echo -e "${YELLOW}🧪 Testing: $test_name${NC}"
    log_message "Starting test: $test_name"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

test_pass() {
    local test_name="$1"
    echo -e "${GREEN}✅ PASS: $test_name${NC}"
    log_message "PASS: $test_name"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    local test_name="$1"
    local error_msg="$2"
    echo -e "${RED}❌ FAIL: $test_name - $error_msg${NC}"
    log_message "FAIL: $test_name - $error_msg"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}This integration test must be run as root (use sudo)${NC}"
        exit 1
    fi
}

# Test: WiFi Manager Python Module Import
test_wifi_manager_import() {
    test_start "WiFi Manager Python Module Import"

    cd "$DEVICE_SOFTWARE_PATH/src/wifi-manager"
    if python3 -c "from wifi_manager import WiFiManager; print('Import successful')" 2>/dev/null; then
        test_pass "WiFi Manager Python Module Import"
    else
        test_fail "WiFi Manager Python Module Import" "Cannot import wifi_manager module"
    fi
}

# Test: Device ID Generation
test_device_id_generation() {
    test_start "Device ID Generation"

    cd "$DEVICE_SOFTWARE_PATH/src/wifi-manager"
    DEVICE_ID=$(python3 -c "from wifi_manager import WiFiManager; wm = WiFiManager(); print(wm.device_id)")

    if [ ${#DEVICE_ID} -eq 8 ] && [[ "$DEVICE_ID" =~ ^[A-Z0-9]+$ ]]; then
        test_pass "Device ID Generation"
        log_message "Generated Device ID: $DEVICE_ID"
    else
        test_fail "Device ID Generation" "Invalid device ID format: '$DEVICE_ID'"
    fi
}

# Test: Configuration File Generation
test_config_generation() {
    test_start "Configuration File Generation"

    cd "$DEVICE_SOFTWARE_PATH/src/wifi-manager"
    python3 -c "
from wifi_manager import WiFiManager
wm = WiFiManager()
wm.create_hostapd_config()
wm.create_dnsmasq_config()
wm.save_config()
"

    if [ -f "$DEVICE_SOFTWARE_PATH/config/hostapd.conf" ] && \
       [ -f "$DEVICE_SOFTWARE_PATH/config/dnsmasq.conf" ] && \
       [ -f "$DEVICE_SOFTWARE_PATH/config/device-config.json" ]; then
        test_pass "Configuration File Generation"
    else
        test_fail "Configuration File Generation" "Configuration files not created"
    fi
}

# Test: Hostapd Configuration Content
test_hostapd_config_content() {
    test_start "Hostapd Configuration Content"

    if [ -f "$DEVICE_SOFTWARE_PATH/config/hostapd.conf" ]; then
        if grep -q "ssid=RNG-Miner-" "$DEVICE_SOFTWARE_PATH/config/hostapd.conf" && \
           grep -q "wpa_passphrase=RNG-Miner-Password-123" "$DEVICE_SOFTWARE_PATH/config/hostapd.conf" && \
           grep -q "interface=wlan0" "$DEVICE_SOFTWARE_PATH/config/hostapd.conf"; then
            test_pass "Hostapd Configuration Content"
        else
            test_fail "Hostapd Configuration Content" "Missing required configuration entries"
        fi
    else
        test_fail "Hostapd Configuration Content" "hostapd.conf file not found"
    fi
}

# Test: Network Interface Configuration (Dry Run)
test_network_interface_config() {
    test_start "Network Interface Configuration Check"

    # Check if wlan0 interface exists
    if ip link show wlan0 > /dev/null 2>&1; then
        test_pass "Network Interface Configuration Check"
        log_message "wlan0 interface detected"
    else
        test_fail "Network Interface Configuration Check" "wlan0 interface not found"
        log_message "WARNING: wlan0 interface not available - this is expected in non-Pi environments"
    fi
}

# Test: Hotspot Start/Stop Commands
test_hotspot_commands() {
    test_start "Hotspot Management Commands"

    cd "$DEVICE_SOFTWARE_PATH/src/wifi-manager"

    # Test status command (should work regardless of actual state)
    if python3 wifi_manager.py status > /dev/null 2>&1; then
        test_pass "Hotspot Management Commands"
    else
        test_fail "Hotspot Management Commands" "WiFi manager status command failed"
    fi
}

# Test: HTTP Server Integration
test_http_server_integration() {
    test_start "HTTP Server Integration"

    cd "$DEVICE_SOFTWARE_PATH/src/http-server"

    # Test HTTP server import and basic functionality
    if python3 -c "
import sys
sys.path.insert(0, '../wifi-manager')
from server import DeviceHTTPServer
server = DeviceHTTPServer()
print('HTTP server integration successful')
" 2>/dev/null; then
        test_pass "HTTP Server Integration"
    else
        test_fail "HTTP Server Integration" "HTTP server cannot integrate with WiFi manager"
    fi
}

# Test: Unit Tests Execution
test_unit_tests() {
    test_start "Unit Tests Execution"

    cd "$DEVICE_SOFTWARE_PATH/tests"

    # Install test dependencies if needed
    pip3 install -q requests pytest pytest-cov 2>/dev/null || true

    # Run unit tests
    if python3 test_wifi_hotspot.py > /dev/null 2>&1; then
        test_pass "Unit Tests Execution"
    else
        test_fail "Unit Tests Execution" "Unit tests failed"
    fi
}

# Test: Script Permissions and Executability
test_script_permissions() {
    test_start "Script Permissions and Executability"

    local scripts_ok=true

    for script in "start-hotspot.sh" "stop-hotspot.sh" "startup.sh" "run-tests.sh"; do
        script_path="$DEVICE_SOFTWARE_PATH/scripts/$script"
        if [ -x "$script_path" ]; then
            log_message "✓ $script is executable"
        else
            log_message "✗ $script is not executable"
            scripts_ok=false
        fi
    done

    if $scripts_ok; then
        test_pass "Script Permissions and Executability"
    else
        test_fail "Script Permissions and Executability" "Some scripts are not executable"
    fi
}

# Test: System Dependencies Check
test_system_dependencies() {
    test_start "System Dependencies Check"

    local deps_ok=true
    local missing_deps=""

    # Check for required packages (they may not be installed in test environment)
    for pkg in "hostapd" "dnsmasq" "iptables"; do
        if dpkg -l | grep -q "^ii  $pkg "; then
            log_message "✓ $pkg is installed"
        else
            log_message "! $pkg is not installed (will be installed on first run)"
            # Don't fail the test for missing packages in test environment
        fi
    done

    # Check for Python dependencies
    for module in "flask" "pyOpenSSL"; do
        if python3 -c "import $module" 2>/dev/null; then
            log_message "✓ Python module $module is available"
        else
            log_message "✗ Python module $module is missing"
            missing_deps="$missing_deps $module"
            deps_ok=false
        fi
    done

    if $deps_ok; then
        test_pass "System Dependencies Check"
    else
        test_fail "System Dependencies Check" "Missing Python dependencies:$missing_deps"
    fi
}

# Test: Configuration Validation
test_configuration_validation() {
    test_start "Configuration Validation"

    # Check if device config exists and is valid JSON
    if [ -f "$DEVICE_SOFTWARE_PATH/config/device-config.json" ]; then
        if python3 -c "
import json
with open('$DEVICE_SOFTWARE_PATH/config/device-config.json', 'r') as f:
    config = json.load(f)
    assert 'device_id' in config
    assert 'hotspot_ssid' in config
    assert len(config['device_id']) == 8
    print('Configuration validation successful')
" 2>/dev/null; then
            test_pass "Configuration Validation"
        else
            test_fail "Configuration Validation" "Invalid configuration file format"
        fi
    else
        test_fail "Configuration Validation" "Device configuration file not found"
    fi
}

# Main test execution
main() {
    echo -e "${YELLOW}🚀 Orange Pi WiFi Hotspot Integration Tests${NC}"
    echo "=================================================="
    log_message "Starting integration tests"

    # Create logs directory
    mkdir -p "$DEVICE_SOFTWARE_PATH/logs"

    # Run all tests
    test_wifi_manager_import
    test_device_id_generation
    test_config_generation
    test_hostapd_config_content
    test_network_interface_config
    test_hotspot_commands
    test_http_server_integration
    test_unit_tests
    test_script_permissions
    test_system_dependencies
    test_configuration_validation

    # Test summary
    echo ""
    echo "=================================================="
    echo -e "${YELLOW}📊 Test Results Summary${NC}"
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        log_message "All integration tests passed"
        exit 0
    else
        echo -e "${RED}💥 Some tests failed${NC}"
        log_message "Integration tests completed with $TESTS_FAILED failures"
        exit 1
    fi
}

# Handle script arguments
case "${1:-run}" in
    "run")
        check_root
        main
        ;;
    "quick")
        # Run subset of tests that don't require root
        echo -e "${YELLOW}🏃 Quick Integration Tests (Non-Root)${NC}"
        test_wifi_manager_import
        test_device_id_generation
        test_script_permissions
        ;;
    *)
        echo "Usage: $0 {run|quick}"
        echo "  run   - Run all integration tests (requires root)"
        echo "  quick - Run quick tests that don't require root"
        exit 1
        ;;
esac
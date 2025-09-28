#!/bin/bash
# Orange Pi Device Software Test Runner
# Runs unit tests and generates coverage reports

set -euo pipefail

# Configuration
DEVICE_SOFTWARE_PATH="/opt/device-software"
TESTS_PATH="$DEVICE_SOFTWARE_PATH/tests"
LOGS_PATH="$DEVICE_SOFTWARE_PATH/logs"

# Logging function
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message"
}

# Install test dependencies
install_test_dependencies() {
    log_message "Installing test dependencies..."
    if [ -f "$TESTS_PATH/requirements-test.txt" ]; then
        pip3 install -r "$TESTS_PATH/requirements-test.txt"
        log_message "Test dependencies installed"
    else
        log_message "WARNING: Test requirements file not found"
    fi
}

# Run unit tests
run_unit_tests() {
    log_message "Running unit tests..."

    cd "$TESTS_PATH"

    # Run tests with coverage
    python3 -m pytest test_http_server.py -v --tb=short

    log_message "Unit tests completed"
}

# Run tests with coverage report
run_tests_with_coverage() {
    log_message "Running tests with coverage report..."

    cd "$TESTS_PATH"

    # Run tests with coverage
    python3 -m pytest test_http_server.py -v --cov=../src/http-server --cov-report=term-missing --cov-report=html:coverage_html

    log_message "Tests with coverage completed"
    log_message "Coverage report generated in coverage_html/"
}

# Lint Python code
lint_code() {
    log_message "Linting Python code..."

    # Check if flake8 is available
    if command -v flake8 >/dev/null 2>&1; then
        flake8 "$DEVICE_SOFTWARE_PATH/src" --max-line-length=100 --ignore=E501,W503
        log_message "Code linting completed"
    else
        log_message "flake8 not installed, skipping linting"
    fi
}

# Main test execution
main() {
    log_message "Starting test execution..."

    # Create logs directory
    mkdir -p "$LOGS_PATH"

    case "${1:-all}" in
        "unit")
            install_test_dependencies
            run_unit_tests
            ;;
        "coverage")
            install_test_dependencies
            run_tests_with_coverage
            ;;
        "lint")
            lint_code
            ;;
        "all")
            install_test_dependencies
            lint_code
            run_tests_with_coverage
            ;;
        *)
            echo "Usage: $0 {unit|coverage|lint|all}"
            echo "  unit     - Run unit tests only"
            echo "  coverage - Run tests with coverage report"
            echo "  lint     - Run code linting"
            echo "  all      - Run all tests and linting (default)"
            exit 1
            ;;
    esac

    log_message "Test execution completed"
}

main "$@"
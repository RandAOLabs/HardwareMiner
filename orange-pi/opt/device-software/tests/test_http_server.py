#!/usr/bin/env python3
"""
Unit tests for Orange Pi HTTP Server
Tests health check, device info, logging, and server lifecycle
"""

import unittest
import json
import time
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, mock_open, MagicMock
import threading
import requests
from urllib3.exceptions import InsecureRequestWarning

# Add the server module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'http-server'))

# Disable SSL warnings for testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    from server import DeviceHTTPServer
except ImportError as e:
    print(f"Could not import server module: {e}")
    sys.exit(1)

class TestDeviceHTTPServer(unittest.TestCase):
    """Test cases for DeviceHTTPServer"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "device-config.json")
        self.server = None
        self.server_thread = None

    def tearDown(self):
        """Clean up test environment"""
        if self.server and hasattr(self.server, 'running'):
            self.server.running = False
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_loading_default(self):
        """Test loading default configuration when no config file exists"""
        server = DeviceHTTPServer(config_path="/nonexistent/path.json")
        self.assertEqual(server.config['http_port'], 8080)
        self.assertEqual(server.config['wifi_state_timeout'], 30)
        self.assertIn('api_rate_limit', server.config)

    def test_config_loading_existing(self):
        """Test loading existing configuration file"""
        test_config = {
            "device_id": "TEST1234",
            "http_port": 9090,
            "custom_setting": "test_value"
        }

        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)

        server = DeviceHTTPServer(config_path=self.config_path)
        self.assertEqual(server.config['http_port'], 9090)
        self.assertEqual(server.config['custom_setting'], "test_value")
        # Defaults should still be present
        self.assertEqual(server.config['wifi_state_timeout'], 30)

    def test_device_id_generation(self):
        """Test device ID generation consistency"""
        server1 = DeviceHTTPServer(config_path=self.config_path)
        device_id1 = server1.device_id

        # Device ID should be 8 characters, uppercase
        self.assertEqual(len(device_id1), 8)
        self.assertTrue(device_id1.isupper())
        self.assertTrue(device_id1.isalnum())

        # Save config and create new server instance
        server1.save_config()
        server2 = DeviceHTTPServer(config_path=self.config_path)
        device_id2 = server2.device_id

        # Device ID should be consistent across instances
        self.assertEqual(device_id1, device_id2)

    @patch('builtins.open', mock_open())
    @patch('os.path.exists', return_value=False)
    def test_device_id_generation_fallback(self, mock_exists):
        """Test device ID generation with fallback when hardware info unavailable"""
        with patch('uuid.getnode', side_effect=Exception("No MAC")):
            server = DeviceHTTPServer(config_path=self.config_path)
            device_id = server.device_id

            # Should still generate valid 8-character ID
            self.assertEqual(len(device_id), 8)
            self.assertTrue(device_id.isupper())

    def test_config_save(self):
        """Test configuration saving"""
        server = DeviceHTTPServer(config_path=self.config_path)
        original_device_id = server.device_id

        server.save_config()

        # Verify config file was created and contains device ID
        self.assertTrue(os.path.exists(self.config_path))
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config['device_id'], original_device_id)
        self.assertEqual(saved_config['http_port'], 8080)

    def test_health_endpoint_mock(self):
        """Test health endpoint response format using Flask test client"""
        server = DeviceHTTPServer(config_path=self.config_path)

        with server.app.test_client() as client:
            response = client.get('/health')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['status'], 'healthy')
            self.assertIn('timestamp', data)
            self.assertIn('device_id', data)
            self.assertIn('uptime', data)
            self.assertIsInstance(data['uptime'], int)

    def test_device_info_endpoint_mock(self):
        """Test device info endpoint response format using Flask test client"""
        server = DeviceHTTPServer(config_path=self.config_path)

        with server.app.test_client() as client:
            response = client.get('/device/info')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertIn('device_id', data)
            self.assertIn('model', data)
            self.assertIn('wifi_state', data)
            self.assertIn('ip_address', data)
            self.assertIn('mining_status', data)
            self.assertIn('uptime', data)
            self.assertIn('timestamp', data)

            self.assertEqual(data['model'], 'Orange Pi Zero 3')
            self.assertEqual(data['wifi_state'], 'unknown')
            self.assertEqual(data['mining_status'], 'not_configured')

    def test_404_error_handling(self):
        """Test 404 error handling"""
        server = DeviceHTTPServer(config_path=self.config_path)

        with server.app.test_client() as client:
            response = client.get('/nonexistent')
            self.assertEqual(response.status_code, 404)

            data = json.loads(response.data)
            self.assertEqual(data['success'], False)
            self.assertEqual(data['error_code'], 'ENDPOINT_NOT_FOUND')
            self.assertIn('timestamp', data)

    def test_logging_setup(self):
        """Test logging configuration"""
        with patch('os.makedirs'):
            with patch('logging.basicConfig') as mock_logging:
                server = DeviceHTTPServer(config_path=self.config_path)
                mock_logging.assert_called_once()

                # Check that logging was configured
                call_args = mock_logging.call_args
                self.assertIn('level', call_args.kwargs)
                self.assertIn('format', call_args.kwargs)
                self.assertIn('handlers', call_args.kwargs)

    @patch('server.crypto')
    @patch('builtins.open', mock_open())
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    @patch('os.chmod')
    def test_certificate_generation(self, mock_chmod, mock_exists, mock_makedirs, mock_open_file, mock_crypto):
        """Test SSL certificate generation"""
        # Mock crypto objects
        mock_key = MagicMock()
        mock_cert = MagicMock()
        mock_crypto.PKey.return_value = mock_key
        mock_crypto.X509.return_value = mock_cert
        mock_crypto.dump_certificate.return_value = b'cert_data'
        mock_crypto.dump_privatekey.return_value = b'key_data'

        server = DeviceHTTPServer(config_path=self.config_path)
        server.generate_self_signed_cert()

        # Verify certificate generation was attempted
        mock_crypto.PKey.assert_called_once()
        mock_crypto.X509.assert_called_once()
        mock_key.generate_key.assert_called_once()
        mock_cert.sign.assert_called_once()

        # Verify file permissions were set
        self.assertEqual(mock_chmod.call_count, 2)

    def test_request_response_times(self):
        """Test that endpoints respond within acceptable time limits"""
        server = DeviceHTTPServer(config_path=self.config_path)

        with server.app.test_client() as client:
            # Test health endpoint response time
            start_time = time.time()
            response = client.get('/health')
            response_time = time.time() - start_time

            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 2.0)  # Should respond within 2 seconds

            # Test device info endpoint response time
            start_time = time.time()
            response = client.get('/device/info')
            response_time = time.time() - start_time

            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 2.0)  # Should respond within 2 seconds

class TestServerLifecycle(unittest.TestCase):
    """Test server lifecycle operations"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "device-config.json")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_signal_handler(self):
        """Test signal handler for graceful shutdown"""
        server = DeviceHTTPServer(config_path=self.config_path)
        server.running = True

        # Simulate signal reception
        server.signal_handler(15, None)  # SIGTERM

        self.assertFalse(server.running)

    @patch('server.logging')
    def test_server_initialization_logging(self, mock_logging):
        """Test that server initialization is properly logged"""
        server = DeviceHTTPServer(config_path=self.config_path)

        # Verify initialization logging occurred
        mock_logging.info.assert_called()

        # Check that device ID was logged
        logged_calls = [call[0][0] for call in mock_logging.info.call_args_list]
        device_id_logged = any('Device ID:' in call for call in logged_calls)
        self.assertTrue(device_id_logged)

class TestErrorScenarios(unittest.TestCase):
    """Test error handling scenarios"""

    def test_config_loading_with_invalid_json(self):
        """Test handling of invalid JSON in config file"""
        test_dir = tempfile.mkdtemp()
        try:
            config_path = os.path.join(test_dir, "invalid-config.json")

            # Create invalid JSON file
            with open(config_path, 'w') as f:
                f.write('{ invalid json }')

            # Should fall back to default config without crashing
            server = DeviceHTTPServer(config_path=config_path)
            self.assertEqual(server.config['http_port'], 8080)

        finally:
            shutil.rmtree(test_dir)

    @patch('server.logging')
    def test_config_save_permission_error(self, mock_logging):
        """Test handling of permission errors during config save"""
        server = DeviceHTTPServer(config_path="/invalid/path/config.json")

        # This should not crash the server
        server.save_config()

        # Error should be logged
        mock_logging.error.assert_called()

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestDeviceHTTPServer))
    test_suite.addTest(unittest.makeSuite(TestServerLifecycle))
    test_suite.addTest(unittest.makeSuite(TestErrorScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
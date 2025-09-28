#!/usr/bin/env python3
"""
Unit tests for Orange Pi WiFi Hotspot Manager
Tests device ID generation, hostapd configuration, DHCP service, and hotspot lifecycle
"""

import unittest
import json
import time
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, mock_open, MagicMock, call
import subprocess

# Add the wifi-manager module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'wifi-manager'))

try:
    from wifi_manager import WiFiManager
except ImportError as e:
    print(f"Could not import wifi_manager module: {e}")
    sys.exit(1)

class TestWiFiManager(unittest.TestCase):
    """Test cases for WiFiManager"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "device-config.json")
        self.wifi_manager = None

    def tearDown(self):
        """Clean up test environment"""
        if self.wifi_manager:
            try:
                self.wifi_manager.stop_hotspot()
            except:
                pass
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_loading_default(self):
        """Test loading default configuration when no config file exists"""
        wifi_manager = WiFiManager(config_path="/nonexistent/path.json")
        self.assertEqual(wifi_manager.config['http_port'], 8080)
        self.assertEqual(wifi_manager.config['wifi_state_timeout'], 30)
        self.assertEqual(wifi_manager.config['hotspot_password'], "RNG-Miner-Password-123")

    def test_config_loading_existing(self):
        """Test loading existing configuration file"""
        test_config = {
            "device_id": "TEST1234",
            "hotspot_ssid": "RNG-Miner-TEST1234",
            "http_port": 9090
        }

        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)

        wifi_manager = WiFiManager(config_path=self.config_path)
        self.assertEqual(wifi_manager.config['http_port'], 9090)
        self.assertEqual(wifi_manager.device_id, "TEST1234")

    def test_device_id_generation_consistency(self):
        """Test device ID generation is consistent across instances"""
        wifi_manager1 = WiFiManager(config_path=self.config_path)
        device_id1 = wifi_manager1.device_id

        # Device ID should be 8 characters, uppercase
        self.assertEqual(len(device_id1), 8)
        self.assertTrue(device_id1.isupper())
        self.assertTrue(device_id1.isalnum())

        # Save config and create new instance
        wifi_manager1.save_config()
        wifi_manager2 = WiFiManager(config_path=self.config_path)
        device_id2 = wifi_manager2.device_id

        # Device ID should be consistent
        self.assertEqual(device_id1, device_id2)

    @patch('builtins.open', mock_open(read_data="Hardware\t: BCM2835\nRevision\t: a020d3\nSerial\t\t: 00000000a1b2c3d4"))
    @patch('socket.gethostname', return_value='orangepi')
    def test_device_id_generation_with_hardware_info(self, mock_hostname):
        """Test device ID generation with mock hardware information"""
        with patch.object(WiFiManager, 'get_interface_mac', return_value='b8:27:eb:12:34:56'):
            wifi_manager = WiFiManager(config_path=self.config_path)
            device_id = wifi_manager.device_id

            # Should generate consistent ID based on hardware info
            self.assertEqual(len(device_id), 8)
            self.assertTrue(device_id.isupper())

            # Generate again with same hardware info - should be identical
            wifi_manager2 = WiFiManager(config_path="/tmp/test_config2.json")
            device_id2 = wifi_manager2.device_id
            self.assertEqual(device_id, device_id2)

    def test_config_save(self):
        """Test configuration saving"""
        wifi_manager = WiFiManager(config_path=self.config_path)
        original_device_id = wifi_manager.device_id

        wifi_manager.save_config()

        # Verify config file was created
        self.assertTrue(os.path.exists(self.config_path))
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config['device_id'], original_device_id)
        self.assertEqual(saved_config['hotspot_ssid'], f"RNG-Miner-{original_device_id}")

    def test_hostapd_config_generation(self):
        """Test hostapd configuration file generation"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.chmod'):
                    result = wifi_manager.create_hostapd_config()

                    self.assertTrue(result)
                    mock_file.assert_called_once()

                    # Verify content written to file
                    written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
                    self.assertIn(f"ssid=RNG-Miner-{wifi_manager.device_id}", written_content)
                    self.assertIn("wpa_passphrase=RNG-Miner-Password-123", written_content)
                    self.assertIn("interface=wlan0", written_content)

    def test_dnsmasq_config_generation(self):
        """Test dnsmasq configuration file generation"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.chmod'):
                    result = wifi_manager.create_dnsmasq_config()

                    self.assertTrue(result)
                    mock_file.assert_called_once()

                    # Verify content written to file
                    written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
                    self.assertIn("interface=wlan0", written_content)
                    self.assertIn("dhcp-range=192.168.12.100,192.168.12.200", written_content)
                    self.assertIn("dhcp-option=3,192.168.12.1", written_content)

    @patch('subprocess.run')
    def test_network_interface_configuration(self, mock_subprocess):
        """Test network interface configuration"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock successful subprocess calls
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = wifi_manager.configure_network_interface()

        self.assertTrue(result)

        # Verify correct commands were called
        expected_calls = [
            call(['sudo', 'ip', 'link', 'set', 'wlan0', 'down'], check=True, capture_output=True),
            call(['sudo', 'ip', 'addr', 'flush', 'dev', 'wlan0'], check=True, capture_output=True),
            call(['sudo', 'ip', 'addr', 'add', '192.168.12.1/24', 'dev', 'wlan0'], check=True, capture_output=True),
            call(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'], check=True, capture_output=True)
        ]

        mock_subprocess.assert_has_calls(expected_calls)

    @patch('subprocess.run')
    def test_network_interface_configuration_failure(self, mock_subprocess):
        """Test network interface configuration failure handling"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock subprocess failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'ip')

        result = wifi_manager.configure_network_interface()

        self.assertFalse(result)

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=False)
    def test_start_hostapd(self, mock_exists, mock_subprocess):
        """Test hostapd service startup"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock successful subprocess calls
        mock_subprocess.return_value = MagicMock(returncode=0, stderr='')

        with patch.object(wifi_manager, 'stop_hostapd', return_value=True):
            result = wifi_manager.start_hostapd()

            self.assertTrue(result)

            # Verify hostapd was started with correct parameters
            mock_subprocess.assert_called_with(
                ['sudo', 'hostapd', '-B', '-P', wifi_manager.hostapd_pid_file, wifi_manager.hostapd_config_path],
                capture_output=True, text=True
            )

    @patch('subprocess.run')
    def test_start_hostapd_failure(self, mock_subprocess):
        """Test hostapd service startup failure"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock subprocess failure
        mock_subprocess.return_value = MagicMock(returncode=1, stderr='hostapd error')

        with patch.object(wifi_manager, 'stop_hostapd', return_value=True):
            result = wifi_manager.start_hostapd()

            self.assertFalse(result)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('builtins.open', mock_open(read_data='12345'))
    @patch('os.remove')
    def test_stop_hostapd(self, mock_remove, mock_exists, mock_subprocess):
        """Test hostapd service stop"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock PID file exists
        mock_exists.return_value = True

        result = wifi_manager.stop_hostapd()

        self.assertTrue(result)

        # Verify kill command was called with PID
        mock_subprocess.assert_any_call(['sudo', 'kill', '12345'], capture_output=True)

        # Verify pkill command was called as backup
        mock_subprocess.assert_any_call(['sudo', 'pkill', '-f', 'hostapd'], capture_output=True)

        # Verify PID file was removed
        mock_remove.assert_called_once()

    @patch('subprocess.run')
    def test_start_dnsmasq(self, mock_subprocess):
        """Test dnsmasq service startup"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock successful subprocess calls
        mock_subprocess.return_value = MagicMock(returncode=0, stderr='')

        with patch.object(wifi_manager, 'stop_dnsmasq', return_value=True):
            result = wifi_manager.start_dnsmasq()

            self.assertTrue(result)

            # Verify dnsmasq was started with correct parameters
            mock_subprocess.assert_called_with(
                ['sudo', 'dnsmasq', '-C', wifi_manager.dnsmasq_config_path, '-x', wifi_manager.dnsmasq_pid_file],
                capture_output=True, text=True
            )

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data='12345'))
    def test_is_hotspot_active_true(self, mock_open_file, mock_exists, mock_subprocess):
        """Test hotspot active status detection - active case"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock ps command success (process exists)
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = wifi_manager.is_hotspot_active()

        self.assertTrue(result)

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=False)
    def test_is_hotspot_active_false(self, mock_exists, mock_subprocess):
        """Test hotspot active status detection - inactive case"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock pgrep command failure (no process found)
        mock_subprocess.return_value = MagicMock(returncode=1)

        result = wifi_manager.is_hotspot_active()

        self.assertFalse(result)

    def test_get_hotspot_status(self):
        """Test hotspot status information retrieval"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        with patch.object(wifi_manager, 'is_hotspot_active', return_value=True):
            with patch.object(wifi_manager, 'get_connected_clients', return_value=[]):
                status = wifi_manager.get_hotspot_status()

                self.assertIsInstance(status, dict)
                self.assertTrue(status['active'])
                self.assertEqual(status['device_id'], wifi_manager.device_id)
                self.assertEqual(status['ssid'], f"RNG-Miner-{wifi_manager.device_id}")
                self.assertEqual(status['ip_address'], "192.168.12.1")
                self.assertIn('timestamp', status)

class TestWiFiManagerIntegration(unittest.TestCase):
    """Integration tests for WiFi manager lifecycle"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "device-config.json")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('builtins.open', mock_open())
    @patch('os.chmod')
    def test_full_hotspot_lifecycle(self, mock_chmod, mock_open_file, mock_makedirs, mock_subprocess):
        """Test complete hotspot start/stop lifecycle"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock all subprocess calls as successful
        mock_subprocess.return_value = MagicMock(returncode=0, stderr='')

        # Mock methods that depend on actual system state
        with patch.object(wifi_manager, 'is_hotspot_active', side_effect=[False, True, False]):
            # Test start hotspot
            result = wifi_manager.start_hotspot()
            self.assertTrue(result)

            # Test hotspot is active
            self.assertTrue(wifi_manager.is_hotspot_active())

            # Test stop hotspot
            result = wifi_manager.stop_hotspot()
            self.assertTrue(result)

            # Test hotspot is inactive
            self.assertFalse(wifi_manager.is_hotspot_active())

    @patch('subprocess.run')
    @patch('time.sleep')  # Speed up tests
    def test_restart_hotspot(self, mock_sleep, mock_subprocess):
        """Test hotspot restart functionality"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock all subprocess calls as successful
        mock_subprocess.return_value = MagicMock(returncode=0, stderr='')

        with patch.object(wifi_manager, 'stop_hotspot', return_value=True) as mock_stop:
            with patch.object(wifi_manager, 'start_hotspot', return_value=True) as mock_start:
                result = wifi_manager.restart_hotspot()

                self.assertTrue(result)
                mock_stop.assert_called_once()
                mock_start.assert_called_once()

class TestErrorScenarios(unittest.TestCase):
    """Test error handling scenarios"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "device-config.json")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_loading_with_invalid_json(self):
        """Test handling of invalid JSON in config file"""
        # Create invalid JSON file
        with open(self.config_path, 'w') as f:
            f.write('{ invalid json }')

        # Should fall back to default config without crashing
        wifi_manager = WiFiManager(config_path=self.config_path)
        self.assertEqual(wifi_manager.config['http_port'], 8080)

    @patch('logging.error')
    def test_config_save_permission_error(self, mock_logging):
        """Test handling of permission errors during config save"""
        wifi_manager = WiFiManager(config_path="/invalid/path/config.json")

        # This should not crash the manager
        wifi_manager.save_config()

        # Error should be logged
        mock_logging.assert_called()

    @patch('subprocess.run')
    def test_hostapd_start_failure_handling(self, mock_subprocess):
        """Test handling of hostapd startup failures"""
        wifi_manager = WiFiManager(config_path=self.config_path)

        # Mock subprocess failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'hostapd')

        with patch.object(wifi_manager, 'create_hostapd_config', return_value=True):
            with patch.object(wifi_manager, 'create_dnsmasq_config', return_value=True):
                with patch.object(wifi_manager, 'configure_network_interface', return_value=True):
                    result = wifi_manager.start_hotspot()

                    self.assertFalse(result)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestWiFiManager))
    test_suite.addTest(unittest.makeSuite(TestWiFiManagerIntegration))
    test_suite.addTest(unittest.makeSuite(TestErrorScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
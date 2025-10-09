#!/usr/bin/env python3
"""
WiFi Connection Script
Handles robust AP teardown and client WiFi connection
Falls back to AP mode on failure
"""

import sys
import time
import logging
import subprocess
from pathlib import Path

# Setup logging
LOG_DIR = Path("/opt/device-software/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "wifi_connect.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_cmd(cmd, check=True, shell=True, timeout=30):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {cmd}")
        return "", -1
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {cmd}")
        logger.error(f"Error: {e.stderr}")
        if check:
            raise
        return e.stderr, e.returncode

def teardown_ap_mode():
    """Completely tear down AP mode services and configuration"""
    logger.info("🔻 TEARDOWN: Stopping AP mode services...")

    # 1. Stop systemd services FIRST (graceful)
    logger.info("Stopping systemd services gracefully...")
    run_cmd("systemctl stop hostapd", check=False)
    run_cmd("systemctl stop dnsmasq", check=False)
    time.sleep(3)  # Give services time to stop gracefully

    # 2. Kill any remaining processes (not too aggressive initially)
    logger.info("Killing remaining AP processes...")
    run_cmd("pkill -f hostapd", check=False)
    run_cmd("pkill -f dnsmasq", check=False)
    time.sleep(2)

    # 3. Reset interface completely (like old-bad-way)
    logger.info("Resetting wlan0 interface...")
    run_cmd("ip addr flush dev wlan0", check=False)
    run_cmd("ip link set dev wlan0 down", check=False)
    time.sleep(2)

    # 4. Bring interface back up (critical - do this BEFORE NetworkManager config)
    logger.info("Bringing wlan0 back up...")
    run_cmd("ip link set dev wlan0 up", check=False)
    time.sleep(2)

    # 5. Re-enable NetworkManager management
    logger.info("Re-enabling NetworkManager management...")
    run_cmd("nmcli device set wlan0 managed yes", check=False)

    # Remove unmanaged config if it exists
    run_cmd("rm -f /etc/NetworkManager/conf.d/99-unmanaged-devices.conf", check=False)
    time.sleep(2)

    # 6. Restart NetworkManager (after interface is up)
    logger.info("Restarting NetworkManager...")
    run_cmd("systemctl restart NetworkManager", check=False)
    time.sleep(5)  # Give NM time to fully restart and detect interfaces

    # 7. Restart systemd-resolved (old-bad-way does this)
    logger.info("Starting systemd-resolved...")
    run_cmd("systemctl start systemd-resolved", check=False)
    time.sleep(2)

    # 8. Ensure WiFi radio is on
    logger.info("Enabling WiFi radio...")
    run_cmd("nmcli radio wifi on", check=False)
    time.sleep(2)

    # 9. Wait for NetworkManager to be fully ready
    logger.info("Waiting for NetworkManager to stabilize...")
    nm_ready = False
    for i in range(10):
        output, rc = run_cmd("nmcli device status | grep wlan0", check=False, timeout=10)
        logger.info(f"NetworkManager check {i+1}/10: {output}")

        if output and rc == 0:
            # Check that wlan0 is not in bad states
            if "unavailable" not in output.lower() and "unmanaged" not in output.lower():
                logger.info("NetworkManager ready!")
                nm_ready = True
                break

        time.sleep(2)

    if not nm_ready:
        logger.warning("NetworkManager may not be fully ready, proceeding anyway...")

    time.sleep(3)  # Extra buffer like old-bad-way's adaptive sleep

    logger.info("✅ AP mode teardown complete")
    return True

def connect_to_wifi(ssid, password):
    """Attempt to connect to WiFi network - following old-bad-way pattern"""
    logger.info(f"🔌 CONNECT: Attempting to connect to '{ssid}'...")

    try:
        # Stop any conflicting services (like old-bad-way does)
        logger.info("Ensuring hostapd and dnsmasq are stopped...")
        run_cmd("systemctl stop hostapd", check=False)
        run_cmd("systemctl stop dnsmasq", check=False)
        time.sleep(2)

        # Restart wpa_supplicant first (old-bad-way pattern)
        logger.info("Restarting wpa_supplicant...")
        run_cmd("systemctl stop wpa_supplicant", check=False)
        time.sleep(2)
        run_cmd("systemctl start wpa_supplicant", check=False)
        time.sleep(3)

        # Give NetworkManager time to settle after wpa_supplicant restart
        time.sleep(2)

        # Scan for the network (with proper waits)
        logger.info("Scanning for WiFi networks...")
        run_cmd("nmcli device wifi rescan", check=False)
        time.sleep(5)  # Wait for scan to complete

        # List available networks for debugging
        logger.info("Checking available networks...")
        avail, avail_rc = run_cmd("nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list", check=False, timeout=15)
        if avail and avail_rc == 0:
            networks_list = [n for n in avail.split('\n') if n.strip()]
            logger.info(f"Found {len(networks_list)} networks, showing top 10:")
            for net in networks_list[:10]:
                logger.info(f"  {net}")
        else:
            logger.warning("No networks found in scan!")

        # Check if SSID is visible
        output, _ = run_cmd(f'nmcli -t -f SSID dev wifi list', check=False)
        if ssid not in output:
            logger.warning(f"SSID '{ssid}' not found in scan results")
            logger.warning("Will attempt connection anyway (might be hidden network)")

        # Delete any existing connection with same name to avoid conflicts
        logger.info(f"Removing any existing connection for '{ssid}'...")
        run_cmd(f'nmcli connection delete "{ssid}"', check=False)
        time.sleep(2)

        # Connect to network (following old-bad-way pattern)
        logger.info(f"Connecting to '{ssid}' using NetworkManager...")
        if password:
            cmd = f'nmcli device wifi connect "{ssid}" password "{password}"'
        else:
            cmd = f'nmcli device wifi connect "{ssid}"'

        output, rc = run_cmd(cmd, timeout=30, check=False)

        if rc != 0:
            logger.error(f"nmcli connect failed with return code {rc}")
            logger.error(f"Output: {output}")

            if not password:
                logger.error("No password provided and initial connection failed")
                return False

            logger.info("Attempting alternative connection method...")
            # Try using nmcli connection add (alternative approach)
            add_result, _ = run_cmd(f'nmcli connection add type wifi con-name "{ssid}" ifname wlan0 ssid "{ssid}"', check=False)
            logger.info(f"Connection add result: {add_result}")

            mod_result1, _ = run_cmd(f'nmcli connection modify "{ssid}" wifi-sec.key-mgmt wpa-psk', check=False)
            logger.info(f"Modify key-mgmt result: {mod_result1}")

            mod_result2, _ = run_cmd(f'nmcli connection modify "{ssid}" wifi-sec.psk "{password}"', check=False)
            logger.info(f"Modify psk result: {mod_result2}")

            up_output, up_rc = run_cmd(f'nmcli connection up "{ssid}"', timeout=30, check=False)
            logger.info(f"Connection up result (rc={up_rc}): {up_output}")
            time.sleep(5)
        else:
            logger.info(f"nmcli connect command succeeded: {output}")

        # Wait for connection to establish (old-bad-way uses 6 iterations of 5 seconds)
        logger.info("Waiting for WiFi connection...")
        connection_established = False
        for attempt in range(6):
            time.sleep(5)

            # Check using nmcli general state (like old-bad-way)
            state_output, state_rc = run_cmd("nmcli -t -f STATE general", check=False, timeout=10)
            logger.info(f"Connection attempt {attempt + 1}/6 - General state: {state_output}")

            if state_output and "connected" in state_output.lower():
                logger.info(f"WiFi connection established after {(attempt + 1) * 5} seconds")
                connection_established = True
                break

        if not connection_established:
            logger.warning("Connection polling completed without detecting 'connected' state")

        # Final connection check (check both WiFi and IP like old-bad-way)
        wifi_check, _ = run_cmd("nmcli -t -f WIFI general", check=False)
        if "enabled" in wifi_check.lower():
            state_check, _ = run_cmd("nmcli -t -f STATE general", check=False)
            if "connected" in state_check.lower():
                # Double-check we have IP
                time.sleep(3)
                ip_output, _ = run_cmd("ip addr show wlan0 | grep 'inet '", check=False)
                if ip_output and "inet " in ip_output and "192.168.4.1" not in ip_output:
                    logger.info(f"✅ Successfully connected to '{ssid}'")
                    logger.info(f"IP Address: {ip_output}")
                    return True

        logger.error("Failed to connect to WiFi after multiple attempts")
        return False

    except Exception as e:
        logger.error(f"WiFi connection error: {e}")
        return False

def start_ap_mode():
    """Restart AP mode as fallback"""
    logger.info("🔄 FALLBACK: Restarting AP mode...")

    try:
        # Try the wifi_manager in multiple locations
        wifi_manager_paths = [
            "/opt/device-software/wifi_manager.py",
            "/root/wifi_manager.py",
            "/opt/device-software/src/wifi-manager/wifi_manager.py"
        ]

        wifi_manager = None
        for path in wifi_manager_paths:
            if Path(path).exists():
                wifi_manager = path
                break

        if not wifi_manager:
            logger.error("Could not find wifi_manager.py")
            return False

        logger.info(f"Using wifi_manager at: {wifi_manager}")
        run_cmd(f"python3 {wifi_manager} start_hotspot", check=False)
        time.sleep(5)

        # Verify AP is running
        output, rc = run_cmd("pgrep -f hostapd", check=False)
        if rc == 0:
            logger.info("✅ AP mode restarted successfully")
            return True
        else:
            logger.error("❌ Failed to restart AP mode")
            return False

    except Exception as e:
        logger.error(f"AP mode restart error: {e}")
        return False

def verify_internet_connectivity():
    """Verify we can reach the internet"""
    logger.info("Verifying internet connectivity...")

    try:
        # Try to ping Google DNS
        output, rc = run_cmd("ping -c 3 -W 5 8.8.8.8", check=False)
        if rc == 0:
            logger.info("✅ Internet connectivity verified")
            return True

        logger.warning("⚠ No internet connectivity")
        return False

    except Exception as e:
        logger.error(f"Internet check error: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        logger.error("Usage: wifi_connect.py <ssid> <password>")
        sys.exit(1)

    ssid = sys.argv[1]
    password = sys.argv[2]

    logger.info("="*60)
    logger.info("WiFi Connection Process Starting")
    logger.info(f"Target SSID: {ssid}")
    logger.info("="*60)

    try:
        # Step 1: Complete AP teardown
        if not teardown_ap_mode():
            logger.error("AP teardown failed, aborting")
            sys.exit(1)

        # Step 2: Attempt WiFi connection
        if connect_to_wifi(ssid, password):
            # Step 3: Verify internet
            verify_internet_connectivity()
            logger.info("="*60)
            logger.info("✅ WiFi connection process completed successfully")
            logger.info("="*60)
            sys.exit(0)
        else:
            # Step 4: Connection failed - fallback to AP
            logger.error("WiFi connection failed, falling back to AP mode...")
            start_ap_mode()
            logger.info("="*60)
            logger.info("⚠ WiFi connection failed - reverted to AP mode")
            logger.info("="*60)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error in WiFi connection process: {e}")
        logger.error("Attempting to restore AP mode...")
        start_ap_mode()
        sys.exit(1)

if __name__ == "__main__":
    main()

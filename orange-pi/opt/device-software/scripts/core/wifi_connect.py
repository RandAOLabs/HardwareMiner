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

def wait_for_condition(condition_func, timeout=10, interval=0.5, description="condition"):
    """Wait for a condition to be true with timeout"""
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            logger.info(f"✓ {description} met after {time.time() - start:.1f}s")
            return True
        time.sleep(interval)
    logger.warning(f"⚠ Timeout waiting for {description} after {timeout}s")
    return False

def teardown_ap_mode():
    """Completely tear down AP mode services and configuration"""
    logger.info("🔻 TEARDOWN: Stopping AP mode services...")

    # 1. Stop systemd services FIRST (graceful)
    logger.info("Stopping systemd services gracefully...")
    run_cmd("systemctl stop hostapd", check=False)
    run_cmd("systemctl stop dnsmasq", check=False)

    # Wait for services to stop (poll instead of blind sleep)
    wait_for_condition(
        lambda: run_cmd("pgrep -f 'hostapd|dnsmasq'", check=False)[1] != 0,
        timeout=5,
        interval=0.3,
        description="AP services to stop"
    )

    # 2. Kill any remaining processes
    logger.info("Ensuring AP processes are stopped...")
    run_cmd("pkill -f hostapd", check=False)
    run_cmd("pkill -f dnsmasq", check=False)
    time.sleep(0.5)

    # 3. Reset interface completely
    logger.info("Resetting wlan0 interface...")
    run_cmd("ip addr flush dev wlan0", check=False)
    run_cmd("ip link set dev wlan0 down", check=False)
    time.sleep(1)

    # 4. Bring interface back up (critical - do this BEFORE NetworkManager config)
    logger.info("Bringing wlan0 back up...")
    run_cmd("ip link set dev wlan0 up", check=False)
    time.sleep(1)

    # 5. Re-enable NetworkManager management
    logger.info("Re-enabling NetworkManager management...")
    run_cmd("nmcli device set wlan0 managed yes", check=False)
    run_cmd("rm -f /etc/NetworkManager/conf.d/99-unmanaged-devices.conf", check=False)
    time.sleep(1)

    # 6. Restart NetworkManager (after interface is up)
    logger.info("Restarting NetworkManager...")
    run_cmd("systemctl restart NetworkManager", check=False)

    # Wait for NetworkManager to be active (poll instead of blind 5s sleep)
    wait_for_condition(
        lambda: run_cmd("systemctl is-active NetworkManager", check=False)[0] == "active",
        timeout=8,
        interval=0.5,
        description="NetworkManager to become active"
    )

    # 7. Restart systemd-resolved
    logger.info("Starting systemd-resolved...")
    run_cmd("systemctl start systemd-resolved", check=False)
    time.sleep(1)

    # 8. Ensure WiFi radio is on
    logger.info("Enabling WiFi radio...")
    run_cmd("nmcli radio wifi on", check=False)

    # Poll for WiFi radio to be enabled
    wait_for_condition(
        lambda: "enabled" in run_cmd("nmcli radio wifi", check=False)[0].lower(),
        timeout=3,
        interval=0.3,
        description="WiFi radio to be enabled"
    )

    # 9. Wait for NetworkManager to detect wlan0 properly
    logger.info("Waiting for NetworkManager to stabilize...")
    nm_ready = wait_for_condition(
        lambda: (
            "unavailable" not in run_cmd("nmcli device status | grep wlan0", check=False)[0].lower() and
            "unmanaged" not in run_cmd("nmcli device status | grep wlan0", check=False)[0].lower() and
            run_cmd("nmcli device status | grep wlan0", check=False)[1] == 0
        ),
        timeout=15,
        interval=1,
        description="NetworkManager to recognize wlan0"
    )

    if not nm_ready:
        logger.warning("NetworkManager may not be fully ready, proceeding anyway...")
        time.sleep(2)  # Small buffer if polling failed

    logger.info("✅ AP mode teardown complete")
    return True

def connect_to_wifi(ssid, password):
    """Attempt to connect to WiFi network - following old-bad-way pattern"""
    logger.info(f"🔌 CONNECT: Attempting to connect to '{ssid}'...")

    try:
        # Stop any conflicting services
        logger.info("Ensuring hostapd and dnsmasq are stopped...")
        run_cmd("systemctl stop hostapd", check=False)
        run_cmd("systemctl stop dnsmasq", check=False)
        time.sleep(1)

        # Restart wpa_supplicant first (old-bad-way pattern)
        logger.info("Restarting wpa_supplicant...")
        run_cmd("systemctl stop wpa_supplicant", check=False)
        time.sleep(1)
        run_cmd("systemctl start wpa_supplicant", check=False)

        # Wait for wpa_supplicant to be active
        wait_for_condition(
            lambda: run_cmd("systemctl is-active wpa_supplicant", check=False)[0] == "active",
            timeout=5,
            interval=0.5,
            description="wpa_supplicant to start"
        )

        # Scan for the network
        logger.info("Scanning for WiFi networks...")
        run_cmd("nmcli device wifi rescan", check=False)

        # Poll for scan completion (faster than blind 5s wait)
        wait_for_condition(
            lambda: len(run_cmd("nmcli -t -f SSID dev wifi list", check=False)[0].split('\n')) > 1,
            timeout=8,
            interval=0.5,
            description="WiFi scan to complete"
        )

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
        time.sleep(1)

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
            time.sleep(2)
        else:
            logger.info(f"nmcli connect command succeeded: {output}")

        # Wait for connection to establish using smart polling with exponential backoff
        logger.info("Waiting for WiFi connection...")
        connection_established = wait_for_condition(
            lambda: "connected" in run_cmd("nmcli -t -f STATE general", check=False, timeout=5)[0].lower(),
            timeout=25,
            interval=1,
            description="WiFi connection to establish"
        )

        if not connection_established:
            logger.warning("Connection polling completed without detecting 'connected' state")

        # Final connection check (check both WiFi and IP)
        wifi_check, _ = run_cmd("nmcli -t -f WIFI general", check=False)
        if "enabled" in wifi_check.lower():
            state_check, _ = run_cmd("nmcli -t -f STATE general", check=False)
            if "connected" in state_check.lower():
                # Wait for IP address with polling (instead of blind 3s sleep)
                ip_ready = wait_for_condition(
                    lambda: (
                        "inet " in run_cmd("ip addr show wlan0 | grep 'inet '", check=False)[0] and
                        "192.168.4.1" not in run_cmd("ip addr show wlan0 | grep 'inet '", check=False)[0]
                    ),
                    timeout=5,
                    interval=0.5,
                    description="IP address assignment"
                )

                if ip_ready:
                    ip_output, _ = run_cmd("ip addr show wlan0 | grep 'inet '", check=False)
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
        # WiFi manager is at the organized location
        wifi_manager = "/opt/device-software/src/wifi-manager/wifi_manager.py"

        if not Path(wifi_manager).exists():
            logger.error(f"Could not find wifi_manager.py at {wifi_manager}")
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

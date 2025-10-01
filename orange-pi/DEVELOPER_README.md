# Orange Pi RNG-Miner Developer Guide

## ⚠️ CRITICAL: Install-Once Philosophy

**THIS IS THE MOST IMPORTANT THING TO UNDERSTAND ABOUT THIS PROJECT**

### The Golden Rule

```
EVERY TEST IS A FRESH INSTALL FROM SCRATCH
NO PATCHES. NO FIXES. NO MANUAL INTERVENTION. EVER.
```

### How Testing Works

1. **Burn Image**: Flash a fresh Orange Pi OS image
2. **Run install.sh**: Execute `sudo ./install.sh` ONCE
3. **Test**: Device must work perfectly after this single command
4. **Wipe**: If anything fails, the entire device is wiped and re-imaged
5. **Repeat**: Fix the code in the repo, then go back to step 1

### What This Means For You

#### ❌ NEVER DO THIS:
- "Just SSH in and fix that one file"
- "Run this quick patch script"
- "Manually restart the service"
- "Edit the config file on the device"
- "Install this missing package"
- "Just run this command to fix it"

#### ✅ ALWAYS DO THIS:
- Fix the problem in `install.sh`
- Commit to git
- Wipe the device completely
- Flash a fresh image
- Run `install.sh` again
- Verify it works

### Why This Philosophy?

1. **Production Reality**: Users get ONE chance to install. If install.sh doesn't work perfectly, they have a bricked device.

2. **No Hidden State**: We can't have "well it works on my device" because every test is identical.

3. **Reproducibility**: Every installation is deterministic and repeatable.

4. **Documentation**: install.sh IS the documentation. Everything is in one place.

5. **Support**: We can't tell users "just run these 5 commands to fix it" - they need a working device.

---

## 🏗️ Project Structure

```
orange-pi/
├── install.sh              # THE ONLY ENTRY POINT - Must be perfect
├── start.sh                # Service startup script (called by systemd)
├── stop.sh                 # Service shutdown script
├── test.sh                 # Diagnostic script (for debugging failed installs)
├── wifi_manager.py         # WiFi hotspot management
├── opt/
│   └── device-software/
│       └── src/
│           └── http-server/
│               └── server.py    # Flask HTTP API server
└── API_DOCUMENTATION.md    # Complete API reference
```

### File Locations After Install

```
/opt/rng-miner/                    # Main installation directory
├── start.sh                       # Startup script
├── stop.sh                        # Shutdown script
├── wifi_manager.py                # WiFi management
└── venv/                          # Python virtual environment

/opt/device-software/              # Device software (HTTP server)
├── src/http-server/server.py      # Main Flask server
├── config/                        # Configuration files
├── data/                          # Persistent data (device ID, etc.)
└── logs/                          # Server logs

/var/log/rng-miner/                # Service logs
├── startup.log                    # Startup sequence logs
└── http-server.log                # HTTP server logs (symlink)

/etc/systemd/system/
└── rng-miner.service              # Systemd service definition
```

---

## 🔧 Development Workflow

### Making Changes

1. **Identify the Problem**
   - Run `test.sh` on the device to diagnose
   - Check logs in `/var/log/rng-miner/`
   - Review `journalctl -u rng-miner`

2. **Fix in install.sh**
   - Edit `install.sh` to fix the root cause
   - DO NOT create a separate "fix" script
   - DO NOT assume any manual intervention

3. **Test the Fix**
   ```bash
   # On your dev machine
   git add install.sh
   git commit -m "Fix: description of what was wrong"

   # On the Orange Pi
   # WIPE EVERYTHING (or re-flash the SD card)
   sudo systemctl stop rng-miner
   sudo rm -rf /opt/rng-miner
   sudo rm -rf /opt/device-software
   sudo userdel -r rng-miner 2>/dev/null || true

   # Fresh install
   git clone <repo>
   cd orange-pi
   sudo ./install.sh

   # Test
   sudo ./test.sh
   ```

4. **Verify Success**
   - Service must start automatically
   - WiFi hotspot must be active (if no network)
   - HTTP server must respond on port 80
   - No manual intervention required

### Common Mistakes

#### Mistake #1: "I'll just fix it on the device"
```bash
# ❌ WRONG
ssh orangepi@device
sudo nano /opt/device-software/src/http-server/server.py
sudo systemctl restart rng-miner
```

**Why this is wrong**: The fix isn't in the repo. Next install will have the same bug.

**Correct approach**: Fix install.sh, wipe device, reinstall.

#### Mistake #2: "I'll create a patch script"
```bash
# ❌ WRONG
# patch.sh
cp fixed-server.py /opt/device-software/src/http-server/
systemctl restart rng-miner
```

**Why this is wrong**: Users won't know to run patch.sh. Install must work on first run.

**Correct approach**: Make install.sh copy the correct file.

#### Mistake #3: "Just document the manual steps"
```markdown
# ❌ WRONG
## Post-Install Steps
1. SSH to the device
2. Run `sudo apt install missing-package`
3. Edit /etc/config.conf and change X to Y
4. Restart the service
```

**Why this is wrong**: This defeats the entire purpose. install.sh must do ALL of this.

**Correct approach**: Add these steps to install.sh.

---

## 🐛 Debugging Failed Installs

### Step 1: Run Diagnostics
```bash
cd /opt/rng-miner
sudo ./test.sh
```

This will show:
- Which services are running
- Server file locations
- Port bindings
- Python dependencies
- Configuration files
- Recent errors

### Step 2: Check Logs
```bash
# Startup sequence
cat /var/log/rng-miner/startup.log

# Server logs
tail -50 /opt/device-software/logs/http-server.log

# Systemd logs
journalctl -u rng-miner -n 100 --no-pager
```

### Step 3: Manual Tests
```bash
# Test server directly
sudo python3 /opt/device-software/src/http-server/server.py

# Test WiFi manager
cd /opt/rng-miner
source venv/bin/activate
python3 -c "from wifi_manager import WiFiManager; WiFiManager().start_hotspot()"

# Check if server is listening
sudo ss -tulpn | grep :80
```

### Step 4: Fix install.sh
Based on what you found, update `install.sh` to handle the issue.

### Step 5: Wipe and Reinstall
```bash
# Nuclear reset
sudo systemctl stop rng-miner
sudo systemctl disable rng-miner
sudo rm /etc/systemd/system/rng-miner.service
sudo systemctl daemon-reload
sudo rm -rf /opt/rng-miner
sudo rm -rf /opt/device-software
sudo rm -rf /var/log/rng-miner
sudo userdel -r rng-miner 2>/dev/null || true

# Fresh install
cd ~/orange-pi
git pull
sudo ./install.sh
```

---

## 📝 Install.sh Architecture

### What install.sh Must Do

1. **System Setup**
   - Update packages
   - Install dependencies (Python, Flask, hostapd, dnsmasq)
   - Configure system services

2. **File Installation**
   - Copy all files from repo to `/opt/rng-miner/`
   - Copy device software to `/opt/device-software/`
   - Verify critical files exist

3. **Network Configuration**
   - Configure NetworkManager
   - Set up WiFi hotspot capability
   - Fix DNS conflicts (port 53)
   - Configure firewall

4. **Service Setup**
   - Create systemd service
   - Enable auto-start
   - Configure proper permissions

5. **Verification**
   - Verify all files in place
   - Start the service
   - Check that it's running
   - Display status to user

### Critical Sections

#### File Copying (Lines 128-156)
```bash
# Copy repo files to /opt/rng-miner
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"

# CRITICAL: Copy device software to correct location
mkdir -p /opt/device-software/src/http-server
cp -r "$SCRIPT_DIR/opt/device-software"/* /opt/device-software/

# VERIFY the server file exists
if [[ ! -f "/opt/device-software/src/http-server/server.py" ]]; then
    error "Server script not found after copy"
fi
```

**Why this matters**: start.sh expects the server at `/opt/device-software/src/http-server/server.py`. If it's not there, the service fails.

#### Service Creation
```bash
# Create systemd service
cat > /etc/systemd/system/rng-miner.service << EOF
[Service]
ExecStart=/opt/rng-miner/start.sh
EOF

systemctl daemon-reload
systemctl enable rng-miner
systemctl start rng-miner
```

**Why this matters**: The service must start automatically on boot. No manual intervention.

---

## 🚀 Adding New Features

### Rule: Everything Goes in install.sh

Want to add a new feature? Here's the checklist:

- [ ] Code works on your dev machine
- [ ] Code is added to the repo
- [ ] install.sh copies the code to the right location
- [ ] install.sh installs any new dependencies
- [ ] install.sh configures any required services
- [ ] Fresh install on clean device works
- [ ] Service starts automatically after reboot
- [ ] test.sh can verify the feature is working
- [ ] API_DOCUMENTATION.md is updated (if adding API endpoints)

### Example: Adding a New Python Module

```bash
# In install.sh, add to the package installation section:

log "📦 Installing new-feature dependencies..."
pip3 install new-python-package

# Copy the new module
cp "$SCRIPT_DIR/new_module.py" "$INSTALL_DIR/"

# Verify it can be imported
python3 -c "import new_module" || error "new_module failed to import"
```

### Example: Adding a New API Endpoint

1. Add the endpoint to `opt/device-software/src/http-server/server.py`
2. Update `API_DOCUMENTATION.md` with the new endpoint
3. Add corresponding method to `RNG-APP/services/device-communication/DeviceApiClient.ts`
4. Test fresh install
5. Verify app can call the new endpoint

---

## 🎯 Quality Standards

### Before Committing to Main

- [ ] install.sh runs successfully on clean device
- [ ] No manual steps required after install.sh
- [ ] Service starts automatically
- [ ] Service survives reboot
- [ ] test.sh reports all green checks
- [ ] Logs show no errors
- [ ] API endpoints respond correctly
- [ ] Changes documented in API_DOCUMENTATION.md (if applicable)

### Testing Checklist

```bash
# 1. Fresh device (or factory reset)
# 2. Clone repo
git clone <repo-url>
cd orange-pi

# 3. Single install command
sudo ./install.sh

# 4. Verify everything works
sudo ./test.sh

# 5. Check service status
sudo systemctl status rng-miner

# 6. Test API endpoints
curl http://localhost/health
curl http://localhost/device/info

# 7. Reboot and verify auto-start
sudo reboot
# (after reboot)
sudo systemctl status rng-miner
sudo ./test.sh
```

---

## 🔐 Security Notes

### No Secrets in Repo

- Never commit WiFi passwords
- Never commit API keys
- Never commit private keys
- These should be configured via the mobile app POST endpoints

### Sudo Requirements

install.sh requires root because it:
- Installs system packages
- Creates systemd services
- Modifies network configuration
- Configures firewall rules

The service itself runs as root to bind to port 80 and manage network interfaces.

---

## 📚 Additional Resources

- **API Reference**: See `API_DOCUMENTATION.md`
- **RNG-APP Integration**: See `../RNG-APP/services/device-communication/DeviceApiClient.ts`
- **Server Code**: See `opt/device-software/src/http-server/server.py`
- **Diagnostics**: Run `sudo ./test.sh` on device

---

## ❓ FAQ

**Q: Can I SSH to the device and edit a file to test a fix?**
A: For quick debugging to understand the problem, yes. But NEVER commit without making it work via install.sh on a fresh device.

**Q: The install failed. Can I just run install.sh again?**
A: No. Wipe everything first. install.sh is designed for clean systems only.

**Q: Can I create a separate "update.sh" script?**
A: No. We don't do updates. Every installation is fresh.

**Q: What if a user's device breaks after a month?**
A: They re-flash the SD card and run install.sh again. Their config is saved in `/opt/device-software/config/` which can be backed up.

**Q: This seems extreme. Why not just patch bugs?**
A: Because we're shipping embedded devices to non-technical users. They can't debug failed installs. install.sh must be bulletproof.

---

## 🎓 Philosophy

This project follows the principle: **"If it's not in install.sh, it doesn't exist."**

Every manual command, every config tweak, every "quick fix" - if it's needed to make the device work, it belongs in install.sh.

The goal is that ANY developer can:
1. Flash a fresh SD card
2. Run `sudo ./install.sh`
3. Have a working RNG-Miner device

No tribal knowledge. No hidden steps. No "well on my device it works because I did X six months ago."

Everything is deterministic, reproducible, and documented in code.

---

*Remember: The device is blown away after EVERY test. Make install.sh perfect on the first run.*

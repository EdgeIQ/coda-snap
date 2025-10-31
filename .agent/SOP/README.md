# Coda Snap - Standard Operating Procedures

This document provides step-by-step operational procedures for building, testing, publishing, and managing the Coda snap.

## Table of Contents

1. [Building the Snap Locally](#building-the-snap-locally)
2. [Publishing to Snap Store](#publishing-to-snap-store)
3. [Running E2E Tests](#running-e2e-tests)
4. [Updating Coda Version](#updating-coda-version)
5. [Configuring Devices for Different Environments](#configuring-devices-for-different-environments)
6. [Debugging Snap Hooks](#debugging-snap-hooks)
7. [Managing Snap Interfaces](#managing-snap-interfaces)
8. [Remote Build and Publishing Workflow](#remote-build-and-publishing-workflow)

---

## Building the Snap Locally

### Prerequisites

- Ubuntu 20.04+ or compatible Linux distribution
- Snapcraft installed (`sudo snap install snapcraft --classic`)
- LXD installed and configured (`sudo snap install lxd && lxd init --auto`)
- OR Multipass installed (`brew install multipass` on macOS)

### SOP: Local Build with LXD

**Purpose**: Build snap on local machine using LXD container

**Steps**:

1. **Set the Coda version**
   ```bash
   export EDGEIQ_CODA_VERSION=4.0.22
   ```

2. **Clean previous builds**
   ```bash
   make clean
   ```

3. **Generate snapcraft.yaml from template**
   ```bash
   make template
   ```
   - Reads `snap/local/snapcraft.template.yaml`
   - Substitutes version variables
   - Writes `snap/snapcraft.yaml`

4. **Build the snap**
   ```bash
   make build
   ```
   - Runs `snapcraft --use-lxd`
   - Downloads Coda binary from EdgeIQ API
   - Packages snap with configuration files
   - Output: `coda_4.0.22_amd64.snap`

5. **Verify the build**
   ```bash
   ls -lh coda_*.snap
   ```

**Expected Output**:
```
-rw-r--r-- 1 user user 45M Jan 15 10:30 coda_4.0.22_amd64.snap
```

**Troubleshooting**:

- **Error: LXD not running**
  ```bash
  sudo lxd init --auto
  sudo lxd start
  ```

- **Error: Network timeout downloading binary**
  - Check internet connection
  - Verify EDGEIQ_API_URL is accessible
  - Check version exists: `curl https://api.edgeiq.io/api/v1/platform/releases`

- **Error: Snapcraft build failed**
  ```bash
  # View detailed logs
  snapcraft --use-lxd --debug
  ```

---

### SOP: Local Build with Multipass

**Purpose**: Build snap in Multipass VM (useful on macOS/Windows or when LXD unavailable)

**Steps**:

1. **Install Multipass** (macOS)
   ```bash
   brew install multipass
   ```

2. **Set the Coda version**
   ```bash
   export EDGEIQ_CODA_VERSION=4.0.22
   ```

3. **Build snap in VM**
   ```bash
   make build-local
   ```

   This will:
   - Check for existing VM, create if needed
   - Install snapcraft in VM
   - Transfer project files to VM
   - Build snap in VM (`snapcraft --destructive-mode`)
   - Transfer snap file back to host
   - Stop VM to free resources

4. **Verify the build**
   ```bash
   ls -lh coda_*.snap
   ```

**Expected Output**:
```
========================================
✓ Build-local completed successfully!
Built snap file: coda_4.0.22_amd64.snap
-rw-r--r-- 1 user user 45M Jan 15 10:30 coda_4.0.22_amd64.snap

Next steps:
  • Run E2E tests:  CODA_SNAP_FILE=coda_4.0.22_amd64.snap make e2e-test-run
  • Clean up VM:    make e2e-test-clean
```

**Troubleshooting**:

- **VM creation fails**
  ```bash
  # Check Multipass status
  multipass version
  multipass list

  # Reset if needed
  multipass delete --all
  multipass purge
  ```

- **Build fails in VM**
  ```bash
  # Access VM to debug
  make vm-shell

  # Check build logs
  cd /home/ubuntu/coda-snap-build
  cat build.log
  ```

---

### SOP: Local Installation and Testing

**Purpose**: Install and test locally-built snap on Ubuntu device

**Steps**:

1. **Install the snap**
   ```bash
   sudo snap install --dangerous coda_4.0.22_amd64.snap
   ```
   - `--dangerous` flag required for local snaps (not signed by store)

2. **Connect interfaces**
   ```bash
   make connect
   ```
   - Connects all required snap interfaces
   - See "Managing Snap Interfaces" section for details

3. **Configure the device**
   ```bash
   sudo snap set coda bootstrap.unique-id=test-device-001
   sudo snap set coda bootstrap.company-id=test-company
   ```

4. **Restart the snap**
   ```bash
   sudo snap restart coda
   ```

5. **Verify installation**
   ```bash
   # Check snap is installed
   snap list coda

   # Check service status
   snap services coda

   # View logs
   sudo snap logs coda -n=50
   ```

**Expected Output**:
```
Name  Version  Rev  Tracking       Publisher  Notes
coda  4.0.22   x1   -              -          devmode

Service         Startup  Current  Notes
coda.agent      enabled  active   -
```

**Uninstalling**:
```bash
sudo snap remove coda
```

---

## Publishing to Snap Store

### Prerequisites

- Snap Store account (https://snapcraft.io)
- Registered snap name (`coda`)
- Publisher permissions
- Snapcraft credentials

### SOP: First-Time Publisher Setup

**Purpose**: Configure authentication for Snap Store publishing

**Steps**:

1. **Login to Snapcraft**
   ```bash
   make login
   ```
   - Opens browser for authentication
   - Exports credentials to `./exported.txt`

2. **Set environment variable**
   ```bash
   export SNAPCRAFT_STORE_CREDENTIALS=$(cat ./exported.txt)
   ```
   - Required for subsequent publish commands

3. **Store credentials securely**
   ```bash
   # Store in secure location (e.g., password manager)
   # DO NOT commit exported.txt to git
   ```

**Security Notes**:
- Credentials file contains sensitive authentication tokens
- Rotate credentials if exposed
- Use CI/CD secrets for automated publishing

---

### SOP: Publishing a Release

**Purpose**: Upload and publish snap to Snap Store

**Prerequisites**:
- Built snap files for all architectures (amd64, arm64, armhf)
- Tested snap with E2E tests
- Snapcraft credentials configured

**Steps**:

1. **Set version and channels**
   ```bash
   export EDGEIQ_CODA_VERSION=4.0.22
   export SNAPCRAFT_CHANNEL="edge,beta,candidate,stable"
   ```

2. **Verify snap files exist**
   ```bash
   ls coda_4.0.22_*.snap
   ```
   Expected:
   ```
   coda_4.0.22_amd64.snap
   coda_4.0.22_arm64.snap
   coda_4.0.22_armhf.snap
   ```

3. **Upload and publish**
   ```bash
   make publish
   ```
   - Uploads all snap files
   - Publishes to specified channels
   - Store performs automated reviews

4. **Verify publication**
   ```bash
   snap info coda
   ```
   - Check version in channels
   - Verify architectures available

**Expected Output**:
```
name:      coda
summary:   EdgeIQ Agent for Device Management
publisher: EdgeIQ
channels:
  stable:    4.0.22  2024-01-15 (x1) 45MB
  candidate: 4.0.22  2024-01-15 (x1) 45MB
  beta:      4.0.22  2024-01-15 (x1) 45MB
  edge:      4.0.22  2024-01-15 (x1) 45MB
```

**Publishing Strategy**:

1. **edge**: Latest development builds (auto-publish from CI)
2. **beta**: Weekly releases for QA testing
3. **candidate**: Release candidates for final validation
4. **stable**: Production releases (manual promotion)

**Promotion Workflow**:
```bash
# Promote from edge to beta
snapcraft promote coda --from-channel=edge --to-channel=beta

# Promote from beta to candidate
snapcraft promote coda --from-channel=beta --to-channel=candidate

# Promote from candidate to stable
snapcraft promote coda --from-channel=candidate --to-channel=stable
```

---

## Running E2E Tests

### Prerequisites

- Multipass installed (`brew install multipass` on macOS)
- Python 3 with pytest (`pip3 install pytest`)
- Mosquitto (optional, runs in VM)

### SOP: Full E2E Test Suite

**Purpose**: Run complete automated test suite with VM lifecycle

**Steps**:

1. **Run full test suite**
   ```bash
   make e2e-test
   ```

   This will:
   - Delete existing test VM (if any)
   - Create new Ubuntu 24.04 VM
   - Install and start mock services
   - Run pytest test suite
   - Delete VM
   - Report results

2. **Review test output**
   - Tests run with verbose output
   - Logs show snap installation, configuration, operation
   - Final summary shows pass/fail status

**Expected Duration**: 5-10 minutes

**Expected Output** (success):
```
========================================
Starting full E2E test suite...
✓ VM created: coda-test-vm
✓ Services ready
✓ Running tests...

tests/test_coda_snap.py::TestCodaSnapInstallation::test_install_coda_snap PASSED
tests/test_coda_snap.py::TestCodaSnapInstallation::test_disk_space_exhaustion_crash PASSED

========================================
✓ Full E2E test suite completed successfully
```

**Troubleshooting**:

- **VM creation fails**
  ```bash
  # Check Multipass
  multipass version
  multipass list

  # Clean up and retry
  make e2e-test-clean
  make e2e-test
  ```

- **Tests fail**
  ```bash
  # View detailed logs
  make e2e-test-logs

  # Check service status
  make e2e-test-status
  ```

---

### SOP: Interactive E2E Testing

**Purpose**: Step-by-step testing with VM preserved for debugging

**Steps**:

1. **Setup test environment**
   ```bash
   make e2e-test-setup
   ```
   - Creates VM
   - Installs mock server and Mosquitto
   - Starts services
   - VM kept running

2. **Run tests**
   ```bash
   make e2e-test-run
   ```
   - Executes pytest suite
   - VM remains running after tests

3. **Debug if needed**
   ```bash
   # Access VM
   make vm-shell

   # Check snap status
   snap list
   snap services coda
   sudo snap logs coda

   # Check mock server
   sudo systemctl status edgeiq-mock-server
   sudo journalctl -u edgeiq-mock-server -n 50

   # Check Mosquitto
   sudo systemctl status mosquitto
   ```

4. **Re-run tests**
   ```bash
   # Make code changes, then re-run
   make e2e-test-run
   ```

5. **Cleanup when done**
   ```bash
   make e2e-test-clean
   ```

---

### SOP: Testing Local Snap Build

**Purpose**: Test locally-built snap before publishing

**Steps**:

1. **Build snap locally**
   ```bash
   export EDGEIQ_CODA_VERSION=4.0.22
   make build-local
   ```

2. **Setup test environment**
   ```bash
   make e2e-test-setup
   ```

3. **Run tests with local snap**
   ```bash
   CODA_SNAP_FILE=./coda_4.0.22_amd64.snap make e2e-test-run
   ```
   - Test suite detects local snap file
   - Installs from local file instead of store

4. **Review results**
   - Check logs for installation success
   - Verify configuration applied
   - Check snap operation

5. **Cleanup**
   ```bash
   make e2e-test-clean
   ```

---

### SOP: E2E Test Troubleshooting

**Purpose**: Diagnose and fix test failures

**Common Issues**:

1. **VM not starting**
   ```bash
   # Check Multipass status
   multipass list
   multipass info coda-test-vm

   # Restart Multipass
   sudo multipass restart

   # Delete and recreate VM
   make e2e-test-clean
   make e2e-test-setup
   ```

2. **Mock server not responding**
   ```bash
   # Access VM
   make vm-shell

   # Check service
   sudo systemctl status edgeiq-mock-server

   # View logs
   sudo journalctl -u edgeiq-mock-server -n 100

   # Restart service
   sudo systemctl restart edgeiq-mock-server

   # Test HTTP endpoint
   curl http://localhost:8080/health
   ```

3. **Snap installation fails**
   ```bash
   # Access VM
   make vm-shell

   # Check snapd
   snap version
   snap changes

   # Manual installation
   sudo snap install --dangerous /home/ubuntu/coda_*.snap

   # View installation logs
   snap tasks --last=install
   ```

4. **Tests timeout**
   - Increase timeout in test code
   - Check VM has sufficient resources (2GB RAM, 2 CPUs)
   - Check network connectivity

---

## Updating Coda Version

### SOP: Update Snap to New Coda Version

**Purpose**: Package new Coda release as snap

**Steps**:

1. **Identify new Coda version**
   - Check EdgeIQ release notes
   - Verify version available at API: `https://api.edgeiq.io/api/v1/platform/releases`

2. **Update version variable**
   ```bash
   export EDGEIQ_CODA_VERSION=4.1.0
   ```

3. **Test build locally**
   ```bash
   make clean build-local
   ```

4. **Run E2E tests**
   ```bash
   CODA_SNAP_FILE=./coda_4.1.0_amd64.snap make e2e-test
   ```

5. **If tests pass, build all architectures**
   ```bash
   make template
   snapcraft remote-build --build-for=amd64,armhf,arm64
   ```

6. **Test each architecture** (if devices available)
   - amd64: Test on Ubuntu Core VM
   - arm64: Test on Raspberry Pi 4
   - armhf: Test on Raspberry Pi 3

7. **Publish to edge channel**
   ```bash
   export SNAPCRAFT_CHANNEL="edge"
   make publish
   ```

8. **Monitor edge channel**
   - Check for user reports
   - Review telemetry
   - Wait 24-48 hours

9. **Promote to beta**
   ```bash
   snapcraft promote coda --from-channel=edge --to-channel=beta
   ```

10. **Continue promotion** (beta → candidate → stable)

**Rollback Procedure**:

If issues found after publishing:

```bash
# Revert to previous version
snapcraft promote coda --from-channel=stable --to-channel=stable --revision=X

# Or close specific channel
snapcraft close coda edge
```

---

## Configuring Devices for Different Environments

### SOP: Configure Device for Production

**Purpose**: Configure Coda snap for production EdgeIQ environment

**Steps**:

1. **Set device identity**
   ```bash
   sudo snap set coda bootstrap.unique-id=<device-serial-number>
   sudo snap set coda bootstrap.company-id=<company-id>
   ```

2. **Set production MQTT broker**
   ```bash
   sudo snap set coda conf.mqtt.broker.host=mqtt.edgeiq.io
   sudo snap set coda conf.mqtt.broker.port=1883
   ```

3. **Set production platform URL**
   ```bash
   sudo snap set coda conf.platform.url=https://api.edgeiq.io/api/v1/platform
   ```

4. **Set MQTT credentials** (if using password auth)
   ```bash
   sudo snap set coda conf.mqtt.broker.password="<encrypted-password>"
   ```

5. **Restart snap**
   ```bash
   sudo snap restart coda
   ```

6. **Verify connection**
   ```bash
   sudo snap logs coda | grep -i "connected"
   ```

---

### SOP: Configure Device for Staging

**Purpose**: Configure Coda snap for staging EdgeIQ environment

**Steps**:

1. **Set device identity**
   ```bash
   sudo snap set coda bootstrap.unique-id=<test-device-id>
   sudo snap set coda bootstrap.company-id=<test-company-id>
   ```

2. **Set staging MQTT broker**
   ```bash
   sudo snap set coda conf.mqtt.broker.host=mqtt.stage.edgeiq.io
   sudo snap set coda conf.mqtt.broker.port=1883
   ```

3. **Set staging platform URL**
   ```bash
   sudo snap set coda conf.platform.url=https://api.stage.edgeiq.io/api/v1/platform
   ```

4. **Restart snap**
   ```bash
   sudo snap restart coda
   ```

---

### SOP: Configure Device with TPM 2.0

**Purpose**: Enable certificate-based authentication with TPM

**Prerequisites**:
- Device with TPM 2.0 chip
- Certificate provisioned in EdgeIQ platform

**Steps**:

1. **Connect TPM interface**
   ```bash
   sudo snap connect coda:tpm :tpm
   ```

2. **Configure device identity**
   ```bash
   sudo snap set coda bootstrap.unique-id=<device-id>
   sudo snap set coda bootstrap.company-id=<company-id>
   ```

3. **Configure for certificate auth**
   ```bash
   sudo snap set coda conf.mqtt.broker.use-tpm=true
   ```

4. **Restart snap**
   ```bash
   sudo snap restart coda
   ```

5. **Verify TPM authentication**
   ```bash
   sudo snap logs coda | grep -i "tpm"
   ```

**Reference**: [EdgeIQ TPM Documentation](https://dev.edgeiq.io/docs/configuring-edge-devices-with-tpm-support-for-enhanced-security)

---

## Debugging Snap Hooks

### SOP: Debug Install Hook

**Purpose**: Troubleshoot issues during snap installation

**Steps**:

1. **View install hook logs**
   ```bash
   journalctl -t coda.hook.install --no-pager
   ```

2. **Check if configuration was set**
   ```bash
   sudo snap get coda bootstrap
   sudo snap get coda conf
   ```

3. **Check if files were copied**
   ```bash
   ls -la /var/snap/coda/common/conf/
   ```

4. **Reinstall snap to re-run install hook**
   ```bash
   sudo snap remove coda
   sudo snap install coda_*.snap --dangerous
   ```

**Common Issues**:

- **MAC address not detected**
  - Check network interfaces: `ip link`
  - Manually set unique-id: `sudo snap set coda bootstrap.unique-id=<id>`

- **Configuration files not copied**
  - Check snap permissions
  - Check disk space: `df -h /var/snap/coda/common`

---

### SOP: Debug Configure Hook

**Purpose**: Troubleshoot configuration changes

**Steps**:

1. **View configure hook logs**
   ```bash
   journalctl -t coda.hook.configure --no-pager
   ```

2. **Test configuration change**
   ```bash
   sudo snap set coda bootstrap.unique-id=test-device
   ```

3. **Check if configuration was written**
   ```bash
   cat /var/snap/coda/common/conf/bootstrap.json
   ```

4. **Verify key translation**
   - Snap key: `bootstrap.unique-id`
   - JSON key: `"unique_id"`

5. **Check service restart**
   ```bash
   sudo systemctl status snap.coda.agent.service
   ```

**Common Issues**:

- **Configuration not applied**
  - Check hook logs for errors
  - Verify JSON syntax in configuration files
  - Check file permissions

- **Service not restarting**
  - Manually restart: `sudo snap restart coda`
  - Check service logs: `sudo snap logs coda`

---

### SOP: Test Hook Changes

**Purpose**: Test hook modifications before publishing

**Steps**:

1. **Modify hook code**
   ```bash
   # Edit snap/hooks/install or snap/hooks/configure
   vim snap/hooks/install
   ```

2. **Build snap**
   ```bash
   export EDGEIQ_CODA_VERSION=4.0.22
   make clean build
   ```

3. **Test in clean environment**
   ```bash
   # Remove existing installation
   sudo snap remove coda

   # Install new snap
   sudo snap install --dangerous coda_4.0.22_amd64.snap

   # View hook logs
   journalctl -t coda.hook.install
   ```

4. **Test configure hook**
   ```bash
   sudo snap set coda bootstrap.unique-id=test-123
   journalctl -t coda.hook.configure
   cat /var/snap/coda/common/conf/bootstrap.json
   ```

5. **Run E2E tests**
   ```bash
   CODA_SNAP_FILE=./coda_4.0.22_amd64.snap make e2e-test
   ```

---

## Managing Snap Interfaces

### SOP: Connect All Required Interfaces

**Purpose**: Grant all permissions needed for full Coda functionality

**Steps**:

1. **Use Makefile target**
   ```bash
   make connect
   ```
   - Connects all interfaces defined in Makefile
   - Safe to run multiple times (idempotent)

2. **Verify connections**
   ```bash
   snap connections coda
   ```

**Expected Output**:
```
Interface              Plug                      Slot         Notes
home                   coda:home                 :home        manual
network                coda:network              :network     -
network-bind           coda:network-bind         :network-bind -
shutdown               coda:shutdown             :shutdown    manual
snapd-control          coda:snapd-control        :snapd-control manual
tpm                    coda:tpm                  :tpm         manual
...
```

**Legend**:
- **-**: Auto-connected
- **manual**: Requires manual connection
- **-** (no slot): Interface not available on system

---

### SOP: Connect Specific Interface

**Purpose**: Grant specific permission

**Steps**:

1. **Identify required interface**
   - See snap manifest: `snap info coda --verbose`
   - Or check documentation

2. **Connect interface**
   ```bash
   sudo snap connect coda:<interface> :<interface>
   ```
   Example:
   ```bash
   sudo snap connect coda:tpm :tpm
   ```

3. **Verify connection**
   ```bash
   snap connections coda | grep <interface>
   ```

4. **Test functionality**
   - Restart snap: `sudo snap restart coda`
   - Check logs: `sudo snap logs coda`

---

### SOP: Disconnect Interface

**Purpose**: Revoke permission

**Steps**:

1. **Disconnect interface**
   ```bash
   sudo snap disconnect coda:<interface>
   ```
   Example:
   ```bash
   sudo snap disconnect coda:tpm
   ```

2. **Verify disconnection**
   ```bash
   snap connections coda | grep <interface>
   ```
   - Should show empty slot

3. **Restart snap**
   ```bash
   sudo snap restart coda
   ```

---

### SOP: Troubleshoot Interface Connection

**Purpose**: Diagnose interface connection issues

**Steps**:

1. **Check if interface exists**
   ```bash
   snap interface <interface>
   ```

2. **Check if snap declares plug**
   ```bash
   snap info coda --verbose | grep plugs -A 50
   ```

3. **Try connection with verbose output**
   ```bash
   sudo snap connect coda:<interface> :<interface> -vv
   ```

4. **Check AppArmor denials**
   ```bash
   sudo dmesg | grep DENIED | grep coda
   ```

5. **View snap logs**
   ```bash
   sudo snap logs coda -n=100
   ```

**Common Issues**:

- **Interface not available**
  - Update snapd: `sudo snap refresh snapd`
  - Some interfaces only available on Ubuntu Core

- **Connection denied**
  - Interface may require store approval
  - Check interface documentation

---

## Remote Build and Publishing Workflow

### SOP: Complete Release Workflow

**Purpose**: Full workflow from build to production release

**Prerequisites**:
- Snapcraft credentials configured
- Testing environment setup
- Version number determined

**Steps**:

1. **Set version**
   ```bash
   export EDGEIQ_CODA_VERSION=4.1.0
   ```

2. **Generate snapcraft.yaml**
   ```bash
   make template
   ```

3. **Trigger remote build**
   ```bash
   snapcraft remote-build \
     --launchpad-accept-public-upload \
     --launchpad-timeout 3600 \
     --build-for=amd64,armhf,arm64
   ```
   - Builds on Launchpad infrastructure
   - Parallel builds for all architectures
   - Timeout: 1 hour per architecture

4. **Wait for builds to complete**
   - Monitor build logs
   - Launchpad sends email notifications

5. **Download built snaps**
   - Snapcraft automatically downloads completed snaps
   - Files: `coda_4.1.0_amd64.snap`, `coda_4.1.0_arm64.snap`, `coda_4.1.0_armhf.snap`

6. **Test amd64 build**
   ```bash
   CODA_SNAP_FILE=./coda_4.1.0_amd64.snap make e2e-test
   ```

7. **Publish to edge channel**
   ```bash
   export SNAPCRAFT_CHANNEL="edge"
   make publish
   ```

8. **Monitor edge channel** (24-48 hours)
   - Check user feedback
   - Review crash reports
   - Monitor telemetry

9. **Promote to beta**
   ```bash
   snapcraft promote coda --from-channel=edge --to-channel=beta
   ```

10. **Beta testing** (1 week)
    - Internal QA validation
    - Customer preview testing

11. **Promote to candidate**
    ```bash
    snapcraft promote coda --from-channel=beta --to-channel=candidate
    ```

12. **Candidate validation** (3-5 days)
    - Final pre-production testing
    - Smoke tests on production-like environments

13. **Promote to stable**
    ```bash
    snapcraft promote coda --from-channel=candidate --to-channel=stable
    ```

14. **Announce release**
    - Update release notes
    - Notify customers
    - Update documentation

---

### SOP: Hotfix Release

**Purpose**: Emergency fix for critical production issue

**Steps**:

1. **Create hotfix branch**
   ```bash
   git checkout -b hotfix/4.0.23
   ```

2. **Apply fix and test**
   ```bash
   # Make code changes
   # Test locally
   export EDGEIQ_CODA_VERSION=4.0.23
   make build-local
   CODA_SNAP_FILE=./coda_4.0.23_amd64.snap make e2e-test
   ```

3. **Remote build**
   ```bash
   make template
   snapcraft remote-build --build-for=amd64,armhf,arm64
   ```

4. **Publish directly to candidate**
   ```bash
   export SNAPCRAFT_CHANNEL="candidate"
   make publish
   ```

5. **Validate hotfix** (2-4 hours)
   - Quick smoke tests
   - Verify fix resolves issue

6. **Promote to stable**
   ```bash
   snapcraft promote coda --from-channel=candidate --to-channel=stable
   ```

7. **Monitor closely** (24 hours)
   - Watch for new issues
   - Prepare rollback if needed

---

## Summary

This SOP documentation provides complete procedures for:

- **Building**: Local and remote build workflows
- **Testing**: E2E testing with Multipass VMs
- **Publishing**: Snap Store release and channel management
- **Configuration**: Device setup for different environments
- **Debugging**: Hook troubleshooting and interface management
- **Operations**: Full release workflow and hotfix procedures

For development guidance, see [../../CLAUDE.md](../../CLAUDE.md).
For technical details, see [../System/README.md](../System/README.md).

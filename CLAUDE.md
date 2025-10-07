# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository builds the EdgeIQ Coda snap package - an edge agent platform for IoT device management on Ubuntu Core. The snap downloads the EdgeIQ Coda binary and edge assets from the EdgeIQ API during build, then packages them with network management tools and snap hooks for configuration management.

## Build System

### Environment Variables

The build process is controlled by environment variables:

- `EDGEIQ_SNAP_NAME`: Snap package name (default: `coda`)
- `EDGEIQ_API_URL`: EdgeIQ API endpoint (default: `https://api.edgeiq.io`)
- `EDGEIQ_CODA_VERSION`: Coda version to download (default: `latest`)
- `SNAPCRAFT_CHANNEL`: Publication channels (default: `"edge,beta,candidate,stable"`)

### Common Build Commands

```bash
# Initial setup (installs snapcraft and LXD)
make setup

# Build snap package for all architectures (amd64, arm64, armhf)
export EDGEIQ_CODA_VERSION=4.0.22
make clean build

# Build without LXD (used in CI)
make build-no-lxd

# Build interactively with shell access
make build-interactive

# Local installation for testing
make install

# Clean build artifacts
make clean
```

### Build Process Details

1. **Template Generation** (`make template`): Generates `snap/snapcraft.yaml` from `snap/local/snapcraft.template.yaml` by substituting environment variables
2. **Snap Build**: Downloads Coda binary and edge assets from EdgeIQ API based on architecture, configures network_configurer to "nmcli" in bootstrap.json
3. **Architecture Mapping**:
   - `x86_64-linux-gnu` → `amd64`
   - `arm-linux-gnueabihf` → `arm7`
   - `aarch64-linux-gnu` → `arm64`

## Snap Architecture

### Apps and Services

- **agent**: Main daemon service that runs the `edge` binary
  - Restart condition: `always`
  - Runs as a simple daemon (not forking)

### Snap Hooks

The snap uses Python hooks located in `snap/hooks/`:

- **install**: Runs on first installation
  - Copies default config files from `$SNAP/conf` to `$SNAP_COMMON/conf`
  - Sets MAC address of first ethernet interface as default `unique-id`
  - Translates config keys from underscore to dash format for snap compatibility
  - Processes `bootstrap.json` and `conf.json`

- **configure**: Runs when snap configuration changes via `snap set`
  - Reads snap configuration via `snapctl get`
  - Translates keys from dash to underscore format for Coda
  - Handles identifier.json creation when company-id and unique-id are set
  - Saves configurations to `$SNAP_COMMON/conf/`

- **post-refresh**: Runs after snap refresh/update
  - Cleans up all files and subdirectories in `$SNAP_COMMON/log`
  - Preserves the log directory itself (only removes contents)
  - Handles errors gracefully (e.g., if log directory doesn't exist)
  - Logs cleanup operations for debugging

### Hook Utilities

Common functionality in `utils/shared/hook_utils.py`:

- **Key Translation**: Snap uses dashes (e.g., `relay-frequency-limit`) while Coda uses underscores (e.g., `relay_frequency_limit`)
- **MAC Address Detection**: `get_mac_of_first_ethernet_failsafe()` with 3 retry attempts
- **Configuration Management**: JSON loading/saving with snapctl integration
- **Config Translation**: Recursive translation between snap and Coda key formats
- **Directory Cleanup**: `cleanup_directory()` removes all contents while preserving directory

### Configuration Model

Configuration keys in snap commands map to nested JSON paths:
- Snap: `snap set coda conf.edge.relay-frequency-limit=10`
- Maps to: `conf.json` → `{"edge": {"relay_frequency_limit": 10}}`

Key configuration files in `$SNAP_COMMON/conf/`:
- `bootstrap.json`: Device bootstrap settings (unique-id, company-id, network_configurer)
- `conf.json`: Runtime configuration
- `identifier.json`: Device identifier (auto-created from company-id + unique-id)

### Snap Plugs

The snap requires numerous plugs for device management capabilities:

**Core System Access**:
- `shutdown`, `snapd-control`, `hardware-observe`, `system-observe`

**Network Management** (required for network configuration features):
- `network`, `network-bind`, `network-control`
- `network-manager`, `network-manager-observe`
- `network-setup-control`, `network-setup-observe`
- `network-status`, `network-observe`
- `modem-manager`, `ppp`, `firewall-control`

**Security & Monitoring**:
- `tpm` (for TPM 2.0 certificate-based auth)
- `log-observe`, `physical-memory-observe`, `mount-observe`
- `ssh-public-keys`, `raw-usb`

Connect all plugs after installation using `make connect`.

## CI/CD

GitHub Actions workflow (`.github/workflows/publish-snap.yml`):

- **Trigger**: Manual workflow dispatch
- **Inputs**: `EDGEIQ_CODA_VERSION`, `SNAPCRAFT_CHANNELS`
- **Environment**: Ubuntu 22.04
- **Build**: Uses `make build-no-lxd` (destructive mode, no LXD container)
- **Publish**: Uses `make publish` with `SNAPCRAFT_STORE_CREDENTIALS` secret

## Remote Build and Publishing

```bash
# Login to snapcraft store
make login
export SNAPCRAFT_STORE_CREDENTIALS=$(cat ./exported.txt)

# Configure and build remotely
export EDGEIQ_CODA_VERSION=4.0.22
make template
snapcraft remote-build --launchpad-accept-public-upload --launchpad-timeout 3600 --build-for=amd64,armhf,arm64

# Publish to store
make publish
```

## E2E Testing Infrastructure

### Test Environment

The E2E test suite uses **Multipass VMs** (not Docker) to provide authentic Ubuntu snap testing:

- **Platform**: Multipass VM with Ubuntu 24.04
- **Why Multipass**: Real snapd behavior, full systemd support, no container limitations
- **Test Runner**: pytest on host (macOS), executes via `multipass exec`
- **Mock Services**: EdgeIQ API mock server runs as systemd service inside VM

### Service Architecture

Mock server runs as a **systemd service** (`edgeiq-mock-server.service`) for:
- **Reliability**: Automatic restart on failure
- **Logging**: Integrated with journald and application logs
- **Management**: Standard systemd commands (start/stop/status/restart)
- **Resource limits**: CPU and memory constraints

### Running E2E Tests

```bash
# Full workflow: create VM, run tests, cleanup (recommended)
make e2e-tests-test-full

# Interactive workflow (keeps VM for debugging)
make e2e-tests-setup    # Create VM and start services
make e2e-tests-test     # Run tests (can run multiple times)
make vm-shell           # Debug inside VM
make e2e-tests-clean    # Cleanup when done

# Run specific test
cd e2e-tests/test-runner
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap.py::TestCodaSnapInstallation::test_install_coda_snap -v

# Check service status
make e2e-tests-status       # View VM and service status
make vm-services-logs       # View service logs (last 50 lines)
make e2e-tests-logs         # Follow logs in real-time

# Service management
make vm-services-start      # Start mock server service
make vm-services-stop       # Stop mock server service
```

### E2E Test Configuration

Environment variables in Makefile:
- `MULTIPASS_VM_NAME`: VM name (default: `coda-test-vm`)
- `MULTIPASS_VM_CPUS`: CPU cores (default: `2`)
- `MULTIPASS_VM_MEMORY`: RAM (default: `2G`)
- `MULTIPASS_VM_DISK`: Disk size (default: `10G`)
- `MOCK_SERVER_PORT`: Mock server port (default: `8080`)
- `MQTT_PORT`: MQTT broker port (default: `1883`)

### Test Components

1. **Multipass VM** (`e2e-tests/cloud-init.yaml`): Ubuntu 24.04 with snapd
2. **Mock Server** (`e2e-tests/mock-server/server.py`): Simulates EdgeIQ API
3. **Test Fixtures** (`e2e-tests/fixtures/`): Mock API responses and configs
4. **Test Suite** (`e2e-tests/test-runner/tests/test_coda_snap.py`): Main test cases

### E2E Test Cases

Tests in `TestCodaSnapInstallation` class run **sequentially** in order:

#### 1. `test_install_coda_snap`
Installs and configures the coda snap from the Snap Store:
- Waits for snapd to be ready
- Installs coda snap from stable channel
- Connects all required snap interfaces (network, tpm, etc.)
- Configures bootstrap settings (company-id, unique-id)
- Configures MQTT broker and platform URL
- Verifies configuration is persisted correctly
- Validates snap is running and logging

#### 2. `test_disk_space_exhaustion_crash`
Reproduces crash behavior when disk space is exhausted (based on production incident):
- **Purpose**: Verify snap crashes predictably when `/var/snap/coda/common` is full
- **Method**: Creates 10MB loop device mounted over entire common directory
- **Expected Behavior**:
  - Snap fails to write logs: "Failed to fire hook: write .../log/...: no space left on device"
  - Database (ledis) fails to initialize due to disk space
  - Fatal error: `level=fatal msg="resource temporarily unavailable"`
  - Process exits with status 1
  - Systemd restart loop: attempts 5 restarts, then gives up
  - Final state: `failed (Result: exit-code)`
- **Cleanup**: Unmounts loop device, restores common directory, verifies snap can restart
- **Key Finding**: Filling only `/var/snap/coda/common/log` is insufficient - must fill entire common directory to trigger crash (affects both logs and database)

#### 3. `test_post_refresh_hook_cleanup`
Validates post-refresh hook log directory cleanup:
- **Purpose**: Verify post-refresh hook cleans up log directory during snap updates
- **Method**: Creates test log files and subdirectories, triggers snap refresh
- **Test Steps**:
  1. Verifies coda snap is installed and running
  2. Creates test log files and subdirectories in `$SNAP_COMMON/log`
  3. Triggers snap refresh (uses revert/refresh if already up-to-date)
  4. Verifies log directory is completely emptied
  5. Confirms snap continues running normally after refresh
- **Expected Behavior**:
  - All log files and subdirectories are removed
  - Log directory itself is preserved (not deleted)
  - Post-refresh hook logs cleanup operations
  - Snap service remains active and functional
- **Key Validations**: Tests file removal, subdirectory removal, directory preservation, and snap stability

### Debugging Failed Tests

```bash
# Check service status first
make e2e-tests-status

# View service logs
make vm-services-logs        # Last 50 lines
make e2e-tests-logs          # Follow in real-time

# Access VM to debug
make vm-shell

# Inside VM, check mock server:
sudo systemctl status edgeiq-mock-server.service
sudo journalctl -u edgeiq-mock-server.service -n 50
curl http://localhost:8080/health

# Inside VM, check snap status:
snap list
snap services coda.agent
snap logs coda.agent -n=100
cat /var/snap/coda/common/conf/bootstrap.json
journalctl -u snap.coda.agent -n 50

# Restart mock server if needed:
sudo systemctl restart edgeiq-mock-server.service
```

## Hook Development

### Hook Architecture

Snap hooks are Python scripts in `snap/hooks/` that use shared utilities from `utils/shared/hook_utils.py`:

- **install** (`snap/hooks/install`): First-time setup
  - Copies default configs from `$SNAP/conf` to `$SNAP_COMMON/conf`
  - Sets MAC address of first ethernet interface as default `unique-id`
  - Translates and stores configs via snapctl

- **configure** (`snap/hooks/configure`): Config change handler
  - Triggered by `snap set coda <key>=<value>`
  - Reads snap config via snapctl, translates keys, saves to JSON files
  - Auto-creates `identifier.json` when both `company-id` and `unique-id` are set

- **post-refresh** (`snap/hooks/post-refresh`): Post-update cleanup
  - Triggered automatically after snap refresh/update
  - Cleans up all contents of `$SNAP_COMMON/log` directory
  - Uses `cleanup_directory()` utility for safe, thorough cleanup
  - Preserves directory structure (only removes contents)

### Key Translation System

**Critical**: Snap uses dashes, Coda uses underscores due to snapd restrictions:

```python
# In hook_utils.py:
translate_config_snap_to_coda(obj)  # dash -> underscore
translate_config_coda_to_snap(obj)  # underscore -> dash

# Example:
# Snap command: snap set coda conf.edge.relay-frequency-limit=10
# JSON output:  conf.json → {"edge": {"relay_frequency_limit": 10}}
```

### Testing Hooks Locally

```bash
# Build and install snap locally
export EDGEIQ_CODA_VERSION=4.0.22
make clean build install

# Test install hook (runs automatically during install)
snap logs coda.agent

# Test configure hook
sudo snap set coda bootstrap.unique-id=test-device-001
sudo snap set coda bootstrap.company-id=12345
snap get coda -d  # View all config
cat /var/snap/coda/common/conf/identifier.json  # Check auto-created file

# Test post-refresh hook
# Create test log files
sudo sh -c 'echo "test log" > /var/snap/coda/common/log/test.log'
sudo mkdir -p /var/snap/coda/common/log/testdir
ls -la /var/snap/coda/common/log/  # Verify test files exist

# Trigger refresh (hook will clean up logs)
sudo snap refresh coda  # or use snap revert/refresh if already up-to-date
ls -la /var/snap/coda/common/log/  # Verify cleanup (should be empty)

# Check hook logs
journalctl -t coda.hook.install
journalctl -t coda.hook.configure
journalctl -t coda.hook.post-refresh
```

### Hook Utility Functions

Common functions in `utils/shared/hook_utils.py`:

- `get_mac_of_first_ethernet_failsafe()`: Get MAC with 3 retries, 5s delay
- `translate_config()`: Recursive key translation
- `snapctl_get(key)`: Read snap configuration
- `snapctl_set(key, json_data)`: Write snap configuration
- `load_json(path)`: Load JSON config file
- `save_json(path, data)`: Save JSON config file
- `cleanup_directory(dir_path)`: Remove all directory contents while preserving directory

## Key Architectural Points

1. **Binary Distribution Model**: The snap doesn't build Coda from source; it downloads pre-built binaries from EdgeIQ API during the snapcraft build process
2. **Configuration Translation Layer**: Snap hook utilities translate between snap's dash-based keys and Coda's underscore-based keys due to snapd restrictions
3. **Network Manager Integration**: Bootstrap config is modified during build to use "nmcli" for network configuration on Ubuntu Core
4. **Multi-Architecture Support**: Single codebase builds for amd64, arm64, and armhf with architecture-specific binary downloads
5. **Persistent Configuration**: All runtime config stored in `$SNAP_COMMON/conf/` which persists across snap updates
6. **Hook-Driven Configuration**: Python hooks (install, configure) manage configuration lifecycle using shared utilities
7. **Identifier Management**: Device identifier auto-created from company-id + unique-id via configure hook
8. **Multipass-Based Testing**: E2E tests use real Ubuntu VMs (not Docker) for authentic snap behavior validation

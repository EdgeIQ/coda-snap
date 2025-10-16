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

### Multi-Architecture Build Pipeline

GitHub Actions workflow (`.github/workflows/publish-snap.yml`) uses a **matrix strategy** to build snaps for multiple architectures in parallel:

**Architecture Support:**
- **amd64**: Intel/AMD 64-bit (x86_64)
- **arm64**: ARM 64-bit (AArch64)
- **armhf**: ARM 32-bit hard-float (ARMv7)

**Workflow Structure:**

**1. Build Job (Matrix):**
- Runs 3 parallel jobs (one per architecture)
- Uses `docker/setup-qemu-action` for cross-architecture emulation
- Uses `diddlesnaps/snapcraft-multiarch-action` for building
- Generates `snap/snapcraft.yaml` from template with version substitution
- Uploads architecture-specific artifacts (retention: 5 days)

**2. Publish Job (Sequential):**
- Depends on all build jobs completing successfully
- Downloads all architecture-specific snap artifacts
- Publishes all snaps to specified channels using `SNAPCRAFT_STORE_CREDENTIALS`
- Uploads to Snap Store with single `snapcraft upload --release` command per snap

**Configuration:**
- **Trigger**: Manual workflow dispatch
- **Inputs**:
  - `EDGEIQ_CODA_VERSION`: Version of Coda to package (e.g., `4.0.22`)
  - `SNAPCRAFT_CHANNELS`: Comma-separated channels (default: `edge,beta,candidate,stable`)
- **Environment**: Ubuntu 22.04 runners
- **Build Method**: QEMU emulation for ARM architectures
- **Expected Duration**: 20-40 minutes (parallel builds, QEMU overhead for ARM)

**Secrets Required:**
- `SNAPCRAFT_STORE_CREDENTIALS`: Snapcraft authentication token (generated via `make login`)

**Triggering a Build:**
1. Navigate to Actions tab in GitHub repository
2. Select "Build & Publish Snap" workflow
3. Click "Run workflow"
4. Enter `EDGEIQ_CODA_VERSION` (e.g., `4.0.22`)
5. Optionally customize `SNAPCRAFT_CHANNELS`
6. Click "Run workflow" button

**Monitoring Builds:**
- Each architecture shows as separate job in Actions UI
- Build artifacts available for download from workflow run page
- Failed builds can be retried individually per architecture

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
make e2e-test

# Interactive workflow (keeps VM for debugging)
make e2e-test-setup    # Create VM and start services
make e2e-test-run      # Run tests (can run multiple times)
make vm-shell          # Debug inside VM
make e2e-test-clean    # Cleanup when done

# Run specific test file
cd e2e-tests/test-runner
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap.py -v  # Snap installation tests
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap_hooks.py -v  # Hooks tests

# Run specific test
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap.py::TestCodaSnapInstallation::test_install_coda_snap -v
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap_hooks.py::TestCodaSnapHooks::test_install_hook_execution -v

# Check service status
make e2e-test-status       # View VM and service status
make vm-services-logs      # View service logs (last 50 lines)
make e2e-test-logs         # Follow logs in real-time

# Service management
make vm-services-start     # Start mock server service
make vm-services-stop      # Stop mock server service
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
4. **Test Suites**:
   - `e2e-tests/test-runner/tests/test_coda_snap.py`: Snap installation and operational tests
   - `e2e-tests/test-runner/tests/test_coda_snap_hooks.py`: Snap hooks (install, configure, post-refresh) tests

### E2E Test Cases

#### Test Suite: `TestCodaSnapInstallation` (test_coda_snap.py)

Tests run **sequentially** in order:

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

#### Test Suite: `TestCodaSnapHooks` (test_coda_snap_hooks.py)

Comprehensive tests for snap hooks. Tests run **sequentially** and must be executed in order:

#### 1. `test_install_hook_execution`
**Purpose**: Verify install hook runs correctly on first snap installation

**Validates**:
- Hook copies default config files from `$SNAP/conf` to `$SNAP_COMMON/conf`
- Creates `bootstrap.json` and `conf.json` in persistent storage
- Sets default `unique-id` to MAC address of first ethernet interface
- Translates config keys from underscore (Coda) to dash (snap) format
- Hook execution logs appear in journalctl

**Test Steps**:
1. Install coda snap from store (stable channel)
2. Connect all required snap interfaces
3. Verify `bootstrap.json` exists at `/var/snap/coda/common/conf/bootstrap.json`
4. Verify `conf.json` exists at `/var/snap/coda/common/conf/conf.json`
5. Parse JSON files and verify structure
6. Extract `unique-id` from bootstrap.json and verify it's a valid MAC address format
7. Verify snapctl configuration matches file contents (with key translation)
8. Check install hook logs: `journalctl -t coda.hook.install`

**Key Validations**: File creation, MAC address format, key translation (dash ↔ underscore), hook logs

---

#### 2. `test_configure_hook_basic_config`
**Purpose**: Verify configure hook handles basic configuration changes

**Validates**:
- Configure hook triggered by `snap set` commands
- Key translation from dash (snap) to underscore (Coda) works correctly
- Configuration persisted to JSON files
- Nested configuration paths work correctly

**Test Steps**:
1. Set simple config: `snap set coda bootstrap.unique-id=test-device-123`
2. Verify config via `snap get coda bootstrap.unique-id`
3. Verify bootstrap.json contains `unique_id` (underscore format)
4. Set nested config: `snap set coda conf.mqtt.broker.host=test-broker.local`
5. Verify conf.json has correct nested structure: `{"mqtt": {"broker": {"host": "test-broker.local"}}}`
6. Check configure hook logs: `journalctl -t coda.hook.configure`

**Key Validations**: Basic config changes, nested paths, key translation, JSON persistence

---

#### 3. `test_configure_hook_identifier_creation`
**Purpose**: Verify configure hook auto-creates identifier.json

**Validates**:
- Setting both `company-id` and `unique-id` triggers identifier.json creation
- identifier.json contains correct data structure
- bootstrap.json updated with `identifier_filepath` pointing to identifier.json
- Configuration loaded correctly after snap restart

**Test Steps**:
1. Set `snap set coda bootstrap.company-id=test-company-001`
2. Set `snap set coda bootstrap.unique-id=test-device-456`
3. Verify `/var/snap/coda/common/conf/identifier.json` exists
4. Parse identifier.json and verify:
   - `company_id` = "test-company-001"
   - `unique_id` = "test-device-456"
5. Parse bootstrap.json and verify:
   - Has `identifier_filepath` pointing to identifier.json
6. Restart snap and verify it loads configuration correctly

**Key Validations**: Auto-creation of identifier.json, correct data structure, file path reference, snap restart

---

#### 4. `test_configure_hook_complex_nested_config`
**Purpose**: Verify configure hook handles deeply nested configurations

**Validates**:
- Multiple nested levels work correctly
- Dash-to-underscore translation applies recursively
- Complex configuration structures persist correctly
- Multiple config types (strings, integers) handled properly

**Test Steps**:
1. Set multiple nested configs:
   - `snap set coda conf.edge.relay-frequency-limit=10`
   - `snap set coda conf.platform.url=http://test-platform.local:8080/api`
   - `snap set coda conf.mqtt.broker.protocol=tcp`
2. Parse conf.json and verify structure with underscores:
   ```json
   {
     "edge": {"relay_frequency_limit": 10},
     "platform": {"url": "http://test-platform.local:8080/api"},
     "mqtt": {"broker": {"protocol": "tcp"}}
   }
   ```
3. Verify `snap get` returns correct values with dashes
4. Check hook logs for any errors

**Key Validations**: Deeply nested config, recursive key translation, multiple data types, error-free execution

---

#### 5. `test_post_refresh_hook_cleanup`
**Purpose**: Verify post-refresh hook cleans log directory on snap updates

**Validates**:
- Post-refresh hook triggered on snap refresh
- All files and subdirectories in `$SNAP_COMMON/log` are removed
- Log directory itself is preserved (not deleted)
- Snap continues running normally after refresh

**Test Steps**:
1. Verify coda snap is installed and running
2. Create test log files and subdirectories in `$SNAP_COMMON/log`
3. Trigger snap refresh (uses revert/refresh if already up-to-date)
4. Verify log directory is completely emptied
5. Verify snap continues running normally after refresh
6. Check post-refresh hook logs: `journalctl -t coda.hook.post-refresh`

**Key Validations**: Complete cleanup, directory preservation, snap stability, hook logs

---

**Running Hooks Tests**:
```bash
# Run all hooks tests
cd e2e-tests/test-runner
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap_hooks.py -vv -s

# Run specific hooks test
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap_hooks.py::TestCodaSnapHooks::test_install_hook_execution -vv -s
```

### Debugging Failed Tests

```bash
# Check service status first
make e2e-test-status

# View service logs
make vm-services-logs        # Last 50 lines
make e2e-test-logs           # Follow in real-time

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

## AI Agent Instructions

You are an elite Ubuntu Core snap development specialist with deep expertise in the snapcraft ecosystem. Your mission is to deliver production-ready snap packages that are secure, maintainable, and thoroughly tested.

### Core Expertise

**Snapcraft Mastery**:
- Snap structure and architecture (apps, services, hooks, plugs, slots)
- Confinement models (strict, classic, devmode) and security implications
- Snap lifecycle management (install, configure, refresh, remove hooks)
- Interface connections and permission management
- Multi-architecture builds (amd64, arm64, armhf)
- Remote build systems and Launchpad integration

**Development Constraints**:
- Python hooks: Standard library ONLY - no external dependencies allowed
- Bash scripting: Critical for automation, testing, and system operations
- Multipass-first approach: Test in real Ubuntu Core VMs for authentic snap behavior
- Integration testing: Always design tests before implementing solutions
- Test execution: Use `make e2e-test` as the entry point for all e2e testing

**Project Context Awareness**:
- You have access to CLAUDE.md which contains critical project-specific guidance
- Always consult CLAUDE.md for snap structure, build process, and configuration patterns
- Follow established patterns in the codebase for consistency
- Respect existing architecture decisions (e.g., binary distribution model, configuration translation layer)

### Operational Protocol

#### 1. Clarification First
When facing unclear requirements or ambiguous tasks:
- Ask specific clarifying questions about:
  - Desired snap behavior and user experience
  - Confinement and security requirements
  - Target architectures and Ubuntu Core versions
  - Integration points with existing snap functionality
- Perform web research on official snapcraft documentation when:
  - Encountering unfamiliar snap interfaces or plugs
  - Implementing new hook types or lifecycle events
  - Dealing with confinement or permission issues
  - Working with new snapcraft features or best practices
- Never proceed with assumptions - validate understanding first

#### 2. Test-Driven Development
For every feature or fix:
1. **Design Integration Test First**: Create end-to-end test scenario that validates the complete user workflow
2. **Implement Solution**: Write code that makes the test pass
3. **Validate with Multipass**: Run tests in real Ubuntu Core VMs using `make e2e-test`
4. **Document Changes**: Update README and relevant documentation

Integration test requirements:
- Test complete snap lifecycle: install → configure → run → verify
- Validate hook behavior and configuration persistence
- Test across target architectures when possible
- Verify interface connections and permissions
- Include negative test cases (error handling, edge cases)
- Use `make e2e-test` command to run e2e tests in Multipass Ubuntu Core VMs

#### 3. Hook Development Standards
**Python Hooks** (install, configure, post-refresh, etc.):
- Use ONLY Python standard library modules
- Implement robust error handling with meaningful messages
- Use `snapctl` for all snap configuration operations
- Follow key translation patterns (dash ↔ underscore) from existing hooks
- Include logging for debugging and troubleshooting
- Handle edge cases (missing files, invalid JSON, network failures)

**Bash Scripts**:
- Follow POSIX compatibility when possible
- Use `set -euo pipefail` for safety
- Implement proper error handling and cleanup
- Add comments explaining non-obvious logic
- Make scripts idempotent where applicable

#### 4. Multipass-First Workflow
Prefer Multipass for:
- Building snaps: Ensures authentic Ubuntu environment with proper snap tooling
- Running integration tests: Clean Ubuntu VMs that match production Ubuntu Core
- Testing multi-architecture builds: Launch ARM64 VMs on supported hardware
- CI/CD simulation: Match production snap environment locally

Multipass best practices:
- Use Ubuntu LTS versions matching target Ubuntu Core releases
- Launch VMs with `--cloud-init` for automated setup and provisioning
- Mount source code directories for rapid development iteration
- Snapshot VMs before testing for quick rollback and repeatability
- Use instance names that reflect their purpose (e.g., `snap-test-amd64`)
- Clean up instances after testing with `multipass delete --purge`
- Leverage `multipass exec` for scripted test automation
- Use sufficient resources: `--cpus 2 --memory 2G --disk 10G` minimum

**Common Multipass Commands**:
```bash
# Launch Ubuntu VM for snap testing
multipass launch 22.04 --name snap-test --cpus 2 --memory 2G --disk 10G

# Mount project directory into VM
multipass mount ./project snap-test:/home/ubuntu/project

# Execute commands in VM
multipass exec snap-test -- snapcraft

# Install and test snap in VM
multipass exec snap-test -- sudo snap install ./my-snap.snap --dangerous

# Transfer files to/from VM
multipass transfer local-file.txt snap-test:/home/ubuntu/
multipass transfer snap-test:/home/ubuntu/build.log ./

# Snapshot before risky operations
multipass stop snap-test
multipass snapshot snap-test --name before-test

# Restore from snapshot if needed
multipass restore snap-test --snapshot before-test

# Clean up when done
multipass delete snap-test
multipass purge
```

#### 5. Documentation Discipline
Update documentation when making user-facing changes:
- **README.md**: Installation, configuration, usage instructions
- **CLAUDE.md**: Development guidance, architecture decisions, build process
- **Inline comments**: Complex logic, snap-specific workarounds, security considerations
- **Commit messages**: Clear description of what changed and why

Documentation should:
- Include concrete examples with expected output
- Explain the "why" behind snap-specific patterns
- Document known limitations and workarounds
- Provide troubleshooting guidance for common issues

### Quality Standards

**Security**:
- Use strict confinement by default, justify any relaxation
- Minimize interface connections - only request necessary plugs
- Validate all external input (snap config, environment variables, files)
- Never expose sensitive data in logs or error messages
- Follow principle of least privilege for snap permissions

**Maintainability**:
- Follow existing code patterns and conventions in the repository
- Keep hooks focused and single-purpose
- Extract common functionality into shared utilities
- Use descriptive variable and function names
- Avoid clever code - prefer clarity over brevity

**Reliability**:
- Handle all error conditions gracefully
- Provide clear error messages with actionable guidance
- Implement retry logic for transient failures (network, file I/O)
- Ensure idempotent operations where possible
- Test edge cases and failure scenarios

### Problem-Solving Approach

1. **Understand**: Read CLAUDE.md, examine existing code, clarify requirements
2. **Research**: Consult snapcraft docs, search for similar solutions, verify best practices
3. **Design Test**: Write integration test that validates desired behavior
4. **Implement**: Write minimal code to pass the test
5. **Validate**: Run tests using `make e2e-test` in Multipass VMs, verify across architectures if relevant
6. **Document**: Update README and inline documentation
7. **Review**: Check against quality standards, ensure no regressions

### Common Snap Patterns

**Configuration Management**:
- Use `snapctl get/set` for all snap configuration
- Translate between snap keys (dashes) and app config (underscores)
- Store persistent config in `$SNAP_COMMON/conf/`
- Validate configuration before applying
- Provide sensible defaults in install hook

**Hook Coordination**:
- Install hook: Initialize default configuration
- Configure hook: Apply configuration changes, restart services if needed
- Post-refresh hook: Handle migration from previous versions
- Use `snapctl` to control service lifecycle

**Multi-Architecture Builds**:
- Use architecture-specific logic when necessary
- Test on actual hardware or QEMU when possible
- Document architecture-specific limitations
- Use snapcraft's architecture filtering in snapcraft.yaml

### Red Flags to Avoid

❌ Installing pip packages or external dependencies in hooks
❌ Using classic confinement without strong justification
❌ Hardcoding paths instead of using snap environment variables
❌ Implementing features without integration tests
❌ Making user-facing changes without updating documentation
❌ Proceeding with unclear requirements instead of asking questions
❌ Ignoring existing patterns and conventions in the codebase
❌ Testing outside Multipass VMs when validating snap behavior
❌ Not using `make e2e-test` command for e2e test execution

You are methodical, security-conscious, and committed to delivering high-quality snap packages. You always validate your understanding before proceeding, design tests before implementing solutions, and ensure your work is properly documented for future maintainers.



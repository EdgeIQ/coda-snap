# Coda Snap E2E Tests

End-to-end testing infrastructure for the EdgeIQ Coda snap package using Multipass VMs with real Ubuntu environments.

## Architecture

The test environment uses Multipass to create authentic Ubuntu VMs with native snapd, providing more accurate testing than containerized environments.

### Components

#### 1. Multipass VM (`coda-test-vm`)
- **OS**: Ubuntu 24.04 LTS
- **Purpose**: Real Ubuntu environment with native snapd for authentic snap testing
- **Configuration**: 2 CPUs, 2GB RAM, 10GB disk (configurable)
- **Provisioning**: Automated via cloud-init
- **Advantages**: Full systemd support, no privileged containers, real snap behavior

#### 2. Mock Server (macOS Host)
- **Runtime**: Python 3 on macOS host
- **Purpose**: Simulates EdgeIQ API backend
- **Port**: 8080
- **Implementation**: Python asyncio with aiohttp
- **Endpoints**: `/health`, `/api/v1/platform/configs_v3/*/*/*.zip`

#### 3. MQTT Broker (macOS Host)
- **Runtime**: Mosquitto on macOS host
- **Port**: 1883
- **Configuration**: Anonymous connections, all topics (`#`)
- **Access**: VM accesses via host gateway IP

#### 4. Test Runner (macOS Host)
- **Runtime**: pytest on macOS host
- **Purpose**: Executes tests against the Multipass VM
- **Method**: Uses `multipass exec` to run commands in VM
- **Framework**: pytest with requests

## Directory Structure

```
e2e-tests/
├── Makefile                     # Multipass orchestration
├── cloud-init.yaml              # VM provisioning config
├── README.md                    # This file
├── logs/                        # Service logs (gitignored)
│   └── .gitkeep
├── fixtures/                    # Test fixtures and mock data
│   ├── mosquitto.conf          # MQTT broker configuration
│   └── responses/              # Mock API response files
│       └── config.json         # Default config response
├── mock-server/                # Mock EdgeIQ API server
│   ├── requirements.txt
│   ├── server.py               # HTTP server implementation
│   └── responses/              # Runtime response directory (symlink to fixtures)
└── test-runner/                # Test execution
    ├── requirements.txt
    └── tests/
        ├── conftest.py         # Pytest fixtures and configuration
        └── test_coda_snap.py   # Main test suite
```

## Prerequisites

- **macOS** (tested on ARM64, should work on Intel)
- **Multipass** - Install via Homebrew: `brew install multipass`
- **Python 3** - For mock server and test runner
- **Mosquitto** - Install via Homebrew: `brew install mosquitto`
- **Internet connection** - For downloading snap packages from store

## Quick Start

### Installation

```bash
# Install Multipass (if not already installed)
make setup

# Install Python dependencies
cd test-runner
pip3 install -r requirements.txt
cd ..

cd mock-server
pip3 install -r requirements.txt
cd ..
```

### Running All Tests

```bash
cd e2e-tests
make test
```

This will:
1. Create a new Multipass VM with Ubuntu 24.04
2. Provision it with snapd via cloud-init
3. Start mock server and MQTT broker on macOS host
4. Run pytest test suite
5. Display test results
6. Clean up VM and stop services

### Running Tests in Development Mode

To keep the VM running for debugging:

```bash
# Run tests but keep VM
make test-keep-vm

# Access the VM
make vm-shell

# When done
make vm-delete
```

## Makefile Targets

### VM Management

```bash
make vm-create       # Create and provision Ubuntu 24.04 VM
make vm-delete       # Delete VM and purge
make vm-shell        # Open interactive shell in VM
make vm-info         # Show VM details (IP, memory, etc.)
make vm-list         # List all Multipass VMs
```

### Service Management

```bash
make services-start  # Start mock server and MQTT on host
make services-stop   # Stop all services
make status          # Show status of services and VMs
```

### Testing

```bash
make test            # Full test suite (create VM → test → cleanup)
make test-verbose    # Run tests with verbose output
make test-keep-vm    # Run tests but keep VM for debugging
```

### Utilities

```bash
make logs            # Show recent service logs
make logs-follow     # Follow service logs in real-time
make clean           # Clean up everything (VM, services, logs)
make help            # Show all available targets
```

## Configuration

### Environment Variables

```bash
# VM Configuration
export MULTIPASS_VM_NAME=coda-test-vm    # VM name
export MULTIPASS_VM_CPUS=2               # CPU cores
export MULTIPASS_VM_MEMORY=2G            # RAM
export MULTIPASS_VM_DISK=10G             # Disk size

# Service Configuration
export MOCK_SERVER_PORT=8080             # Mock server port
export MQTT_PORT=1883                    # MQTT broker port
```

### Mock Server Endpoints

- **Health Check**: `GET http://localhost:8080/health` (from host)
- **Health Check**: `GET http://<host-ip>:8080/health` (from VM)
- **Config Download**: `GET http://<host-ip>:8080/api/v1/platform/configs_v3/{carrier}/{filename}.zip`

The mock server returns a zip file containing `config.json` from `fixtures/responses/config.json`.

### MQTT Broker

- **Host (from VM)**: `<host-gateway-ip>` (automatically detected)
- **Port**: `1883`
- **Authentication**: Anonymous (no credentials required)

## Usage Examples

### Running Specific Tests

```bash
# Create VM and start services first
make vm-create
make services-start

# Run specific test
cd test-runner
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap.py::TestCodaSnapInstallation::test_install_coda_snap -v

# Cleanup when done
cd ..
make services-stop
make vm-delete
```

### Manual Testing in VM

```bash
# Create VM and enter shell
make vm-create
make vm-shell

# Inside VM:
snap list
snap install hello-world
snap install coda
snap services coda.agent
snap logs coda.agent -n=100

# Exit VM
exit

# Cleanup
make vm-delete
```

### Debugging Failed Tests

```bash
# Run tests and keep VM
make test-keep-vm

# Access VM for inspection
make vm-shell

# Inside VM, check snap status:
snap list
snap services coda.agent
snap logs coda.agent -n=100
snap get coda -d

# View config files
cat /var/snap/coda/common/conf/bootstrap.json
cat /var/snap/coda/common/conf/conf.json
cat /var/snap/coda/common/conf/identifier.json

# Check systemd status
journalctl -u snap.coda.agent -n 50

# Exit and cleanup when done
exit
make vm-delete
```

### Viewing Service Logs

```bash
# Show recent logs
make logs

# Follow logs in real-time
make logs-follow

# View specific log files
tail -f logs/mock-server.log
tail -f logs/mosquitto.log
```

## Test Suite

The test suite (`test_coda_snap.py`) currently verifies:

1. **Snapd Readiness**: Validates snapd service is responsive in VM
2. **Snap Store Access**: Tests connectivity to snap store
3. **Hello-world Installation**: Simple connectivity test
4. **Coda Snap Installation**: Installs coda snap from store
5. **Installation Verification**: Confirms snap is installed correctly

## Troubleshooting

### Multipass VM Fails to Create

**Symptom**: `multipass launch` fails or times out

**Solutions**:
```bash
# Check Multipass status
multipass version
multipass list

# Restart Multipass service (macOS)
sudo launchctl stop com.canonical.multipassd
sudo launchctl start com.canonical.multipassd

# Check system resources
multipass get local.driver
```

### VM Cannot Access Host Services

**Symptom**: Tests fail with connection refused to mock server or MQTT

**Solutions**:
```bash
# Verify services are running on host
make status

# Check host IP from VM perspective
make vm-shell
ip route show default

# Test connectivity from VM
curl http://$(ip route | grep default | awk '{print $3}'):8080/health

# Check macOS firewall settings
# System Preferences → Security & Privacy → Firewall
# Allow incoming connections for Python and Mosquitto
```

### Snap Installation Fails

**Symptom**: `snap install coda` fails with connection errors

**Solutions**:
```bash
# Check VM internet connectivity
make vm-shell
ping -c 3 api.snapcraft.io
snap find coda

# Check snap store status
# Visit: https://status.snapcraft.io/

# Increase timeout in test file
# Edit test_coda_snap.py, increase timeout parameter
```

### Tests Timeout Waiting for Services

**Symptom**: Tests fail with "service did not become ready"

**Solutions**:
```bash
# Check services are actually running
make status
ps aux | grep python3
ps aux | grep mosquitto

# Manually test services
curl http://localhost:8080/health
nc -zv localhost 1883

# Check service logs
make logs

# Restart services
make services-stop
make services-start
```

### Snapd Not Ready in VM

**Symptom**: `snap version` fails or times out

**Solutions**:
```bash
# Access VM and check snapd
make vm-shell
systemctl status snapd
journalctl -u snapd -n 50

# Wait for snap seed
snap wait system seed.loaded

# Refresh snapd
snap refresh snapd
```

## Cleanup

```bash
# Clean everything (recommended after each test run)
make clean

# Manual cleanup if needed
make services-stop
make vm-delete
rm -rf logs/*.log
```

## CI/CD Integration

For GitHub Actions or other CI systems, you would need to:

1. Use a Linux runner (Multipass works on Linux too)
2. Install Multipass via snap
3. Run tests with automated cleanup

Example GitHub Actions workflow:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Multipass
        run: |
          sudo snap install multipass
          multipass version

      - name: Install Dependencies
        run: |
          cd e2e-tests
          pip3 install -r test-runner/requirements.txt
          pip3 install -r mock-server/requirements.txt
          sudo apt-get update
          sudo apt-get install -y mosquitto

      - name: Run E2E Tests
        run: |
          cd e2e-tests
          make test

      - name: Cleanup
        if: always()
        run: |
          cd e2e-tests
          make clean
```

## Development Workflow

### Adding New Tests

1. Add test functions to `test-runner/tests/test_coda_snap.py`
2. Use fixtures from `conftest.py` for VM access and service URLs
3. Use the `exec_command` helper method for running commands in VM
4. Run tests: `make test-keep-vm` for faster iteration

### Updating Mock Server Behavior

1. Modify `mock-server/server.py` to add new endpoints or change behavior
2. Update mock responses in `fixtures/responses/`
3. Restart service: `make services-stop && make services-start`
4. Test changes: Re-run tests

### Customizing Mock Responses

To customize the config response returned by the mock server:

1. Edit `e2e-tests/fixtures/responses/config.json`
2. Restart mock server: `make services-stop && make services-start`

The mock server will automatically package this JSON into a zip file when responding to config download requests.

## Migration Notes

This test infrastructure was migrated from Docker containers to Multipass VMs to provide:

- **Authentic Environment**: Real Ubuntu with native snapd (not containerized simulation)
- **Better Testing**: More accurate representation of production Ubuntu Core behavior
- **Simpler Architecture**: No privileged containers or cgroup workarounds
- **Improved Reliability**: Full systemd support without container limitations

Previous Docker-based infrastructure has been removed. For historical reference, see git history.

## Known Limitations

1. **Snap Store Dependency**: Tests require internet access to install snap from store
2. **Platform**: Currently designed for macOS (can be adapted for Linux)
3. **VM Creation Time**: Initial VM creation takes ~90 seconds
4. **Architecture**: Tests on host architecture (arm64 on Apple Silicon, amd64 on Intel)

## Future Enhancements

- [ ] Add MQTT message verification tests
- [ ] Test snap configuration persistence across VM restarts
- [ ] Add performance tests for agent operations
- [ ] Test network manager integration
- [ ] Add support for testing locally-built snap packages
- [ ] Multi-architecture testing with cross-arch VMs
- [ ] Automated security scanning of snap
- [ ] VM snapshot support for faster test iterations

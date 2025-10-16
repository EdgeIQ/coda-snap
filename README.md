# EdgeIQ Coda Snap

Welcome to the official repository for EdgeIQ Coda snap, formerly known as Edge Local Service. Coda by EdgeIQ is a sophisticated edge agent platform designed to streamline the connection, management, and orchestration of IoT devices at the edge. This snap package equips users with the essential tools to deploy and operate the Coda Edge Agent on Ubuntu Core systems efficiently.

## Key Features

- **Efficient IoT Device Management:** Coda ensures a seamless data flow and secure communication between IoT devices and the EdgeIQ Symphony platform.
- **Robust Monitoring:** Offers comprehensive features for device monitoring, data collection, vital for edge computing solutions.
- **Flexible Integration:** Supports various edge protocols and can be integrated with multiple cloud services, offering versatile workflows for IoT device orchestration.
- **Simplified Deployment:** The snap package facilitates easy deployment on Ubuntu Core, minimizing setup efforts for users.

## Getting Started

### Installation

To install Coda, run the following command in your terminal:

```bash
sudo snap install coda
```

### Basic Configuration

Configure your device with a unique ID and company ID using the following commands:

```bash
sudo snap set coda bootstrap.unique-id=your-unique-id
sudo snap set coda bootstrap.company-id=your-company-id
sudo snap restart coda
```

> **Note:** By default, during the installation, Snap tries to use the MAC address of the first Ethernet port as the `unique-id`. This will happen only one time during the first installation and then can be changed via the `snap set` command.

### Change MQTT Password

To update the MQTT broker password:

```bash
sudo snap set coda conf.mqtt.broker.password="your-encrypted-password"
sudo snap restart coda
```

### Connect to a different environment

To connect to a different EdgeIQ environment, run the following command to set the corresponding broker:

```bash
sudo snap set coda conf.mqtt.broker.host="mqtt.edgeiq.io"
sudo snap restart coda
```

The brokers are:

| Environment | MQTT Broker       |
|------------|-------------------|
| Production | mqtt.edgeiq.io     |
| Staging    | mqtt.stage.edgeiq.io    |

## Configuration

### Configuration Keys

The snap configuration keys correspond to paths in the configuration files, with hyphens instead of underscores due to snapd restrictions. For example, `edge.relay_frequency_limit` in `conf.json` translates to `snap set conf.edge.relay-frequency-limit=10`.

### Viewing Configuration Files

```bash
sudo snap get coda "bootstrap"
cat /var/snap/coda/common/conf/bootstrap.json
cat /var/snap/coda/common/conf/identifier.json

sudo snap get coda "conf"
cat /var/snap/coda/common/conf/conf.json
```

### Persistent Logging

To enable persistent logging for the system journal, which ensures logs are preserved across reboots:

```bash
sudo snap set system journal.persistent=true
```

This configuration is recommended for maintaining log history and debugging purposes.

## Use-cases

### Reboot or Shutdown the Device

To grant access the coda snap to reboot or shutdown the device, please connect the following plugs:

```bash
sudo snap connect coda:shutdown :shutdown
```

### Managing Snaps on the Device

To [manage snaps on the device](https://dev.edgeiq.io/docs/example-managing-snaps-on-ubuntu-core-devices), please connect the following plugs:

```bash
sudo snap connect coda:snapd-control :snapd-control
```

### Network Configuration

To have ability [create and apply network configurations](https://dev.edgeiq.io/docs/create-and-apply-a-network-configuration-for-a-gateway-device) to your device via [API](https://dev.edgeiq.io/docs/network-configuration), please connect the following plug:

```bash
sudo snap connect coda:network-control :network-control
sudo snap connect coda:network-manager :network-manager
sudo snap connect coda:network-manager-observe :network-manager-observe
sudo snap connect coda:firewall-control :firewall-control
```

> **Note:** At this time `modem-manager` is reserved but not supported by the Coda. We are working on adding support for it in nearest the future.

### Certificate-Based Authentication with TPM 2.0

To [configure your Device with TPM Support for Enhanced Security](https://dev.edgeiq.io/docs/configuring-edge-devices-with-tpm-support-for-enhanced-security) , please connect the following plug:

```bash
sudo snap connect coda:tpm :tpm
```

## Development

### Prerequisites

- [Make](https://www.gnu.org/software/make/)
- [Ubuntu 20+](https://ubuntu.com/)
- [Snapcraft](https://snapcraft.io/snapd)

### Setup

To set up your development environment:

```bash
make setup
```

### Build

To build the project:

```bash
make clean build
```

To build a specific version:

```bash
export EDGEIQ_CODA_VERSION=4.0.22
make clean build
```

### Local Installation

To install the locally built snap:

```bash
make install
```

### Remote Build and Publishing

```bash
# Login to the snapcraft store
make login
export SNAPCRAFT_STORE_CREDENTIALS=$(cat ./exported.txt)

# Configure snapcraft.yaml
export EDGEIQ_CODA_VERSION=4.0.22
make template

# Trigger the remote build
snapcraft remote-build --launchpad-accept-public-upload --launchpad-timeout 3600 --build-for=amd64,armhf,arm64

# Publish to the snapcraft store
make publish
```

## E2E Testing

The E2E test suite uses **Multipass VMs** with real Ubuntu environments for authentic snap testing, providing more accurate validation than containerized environments.

### Prerequisites

- [Multipass](https://multipass.run/) - `brew install multipass` (macOS)
- Python 3 with pytest
- [Mosquitto](https://mosquitto.org/) - `brew install mosquitto` (macOS)

### Running Tests

```bash
# Full test workflow (create VM, test, cleanup)
make e2e-test

# Interactive workflow (keeps VM for debugging)
make e2e-test-setup    # Create VM and start services
make e2e-test-run      # Run tests
make vm-shell          # Access VM for debugging
make e2e-test-clean    # Cleanup when done

# Run specific test
cd e2e-tests/test-runner
MULTIPASS_VM_NAME=coda-test-vm pytest tests/test_coda_snap.py::TestClass::test_name -v
```

### Test Architecture

- **Multipass VM**: Ubuntu 24.04 with native snapd (2 CPUs, 2GB RAM, 10GB disk)
- **Mock Server**: Python-based EdgeIQ API simulator running in VM (port 8080)
- **MQTT Broker**: Can run Mosquitto in VM if needed (port 1883)
- **Test Runner**: pytest on host, executes via `multipass exec`

### Common Commands

```bash
make e2e-test-status   # View VM and service status
make e2e-test-logs     # View service logs
make vm-info           # Show VM details
make e2e-test-clean    # Complete cleanup
make vm-list           # List all Multipass VMs
```

For detailed E2E testing documentation, see the [Makefile](e2e-tests/Makefile) and test files in `e2e-tests/test-runner/tests/`.

## Hook Development

The snap uses Python hooks in `snap/hooks/` for configuration management:

- **install**: First-time setup, copies default configs, sets MAC-based unique-id
- **configure**: Handles `snap set` commands, translates config keys, manages identifier.json

Key utilities are in `utils/shared/hook_utils.py` for config translation between snap's dash-based keys and Coda's underscore-based keys.

### Testing Hooks

```bash
# Build and install locally
export EDGEIQ_CODA_VERSION=4.0.22
make clean build install

# Test configuration
sudo snap set coda bootstrap.unique-id=test-device-001
sudo snap set coda bootstrap.company-id=12345
snap get coda -d

# Check logs
journalctl -t coda.hook.install
journalctl -t coda.hook.configure
```

## Architecture Notes

- **Binary Distribution**: Downloads pre-built Coda binaries from EdgeIQ API during build
- **Configuration Translation**: Hook utilities translate between snap (dash) and Coda (underscore) key formats
- **Multi-Architecture**: Builds for amd64, arm64, armhf with architecture-specific binary downloads
- **Network Manager**: Uses nmcli for network configuration on Ubuntu Core
- **Persistent Config**: All runtime config in `$SNAP_COMMON/conf/` persists across updates

For detailed technical documentation and development guidance, see [CLAUDE.md](CLAUDE.md).

For more information and support, visit the [EdgeIQ documentation](https://dev.edgeiq.io/).

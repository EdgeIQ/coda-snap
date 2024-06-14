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
sudo snap set coda bootstrap.unique-id=testdevice
sudo snap set coda bootstrap.company-id=machineshop
sudo snap restart coda
```

### Change MQTT Password

To update the MQTT broker password:

```bash
sudo snap set coda conf.mqtt.broker.password="your-encrypted-password"
sudo snap restart coda
```

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

## Development

### Prerequisites

- [Make](https://www.gnu.org/software/make/)
- [Ubuntu 20+](https://ubuntu.com/)
- [Snapd](https://snapcraft.io/snapd)

### Setup

To set up your development environment:

```bash
make setup
```

### Build

To build the project:

```bash
make uninstall clean build install
```

For more information and support, visit the [EdgeIQ documentation](https://dev.edgeiq.io/).
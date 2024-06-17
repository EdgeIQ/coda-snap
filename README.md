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

## Use-cases

### Reboot or Shutdown the Device

To grant access the coda snap to reboot or shutdown the device, please connect the following plugs:

```bash
sudo snap connect coda:shutdown :shutdown
```

### Managing Snaps on the Device

To [manage snaps on the device](https://dev.edgeiq.io/docs/example-managing-snaps-on-ubuntu-core-devices), please connect the following plugs:

```bash
sudo snap connect coda:snapd-control :snapd-control # required
sudo snap connect coda:snap-refresh-observe :snap-refresh-observe # nice to have
sudo snap connect coda:snap-refresh-control :snap-refresh-control # nice to have
```

### Network Configuration

To have ability [create and apply network configurations]()https://dev.edgeiq.io/docs/create-and-apply-a-network-configuration-for-a-gateway-device to your device via [API](https://dev.edgeiq.io/docs/network-configuration), please connect the following plug:

```bash
sudo snap connect coda:network-control :network-control 
sudo snap connect coda:network-manager :network-manager
sudo snap connect coda:network-manager-observe :network-manager-observe
sudo snap connect coda:firewall-control :firewall-control
```

> **Note:** At this time `modem-manager` is reserved but not actively supported by the Coda. We are working on adding support for it in nearest the future.

### Certificate-Based Authentication with TPM 2.0

To [configure your Device with TPM Support for Enhanced Security](https://dev.edgeiq.io/docs/configuring-edge-devices-with-tpm-support-for-enhanced-security) , please connect the following plug:

```bash
sudo snap connect coda:tpm :tpm
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
# Coda Snap - EdgeIQ Edge Agent

## Overview

**Coda Snap** is the EdgeIQ edge agent packaged as a Ubuntu Core snap. It is THE device agent that runs on edge devices (gateways) to connect them to the EdgeIQ Symphony platform, enabling comprehensive IoT device management, monitoring, and orchestration capabilities.

This snap package represents the core runtime component that EdgeIQ deploys on customer edge devices in production environments.

## What is Coda?

Coda (formerly Edge Local Service) is EdgeIQ's sophisticated edge agent platform designed to:

- **Connect** IoT devices to the EdgeIQ Symphony platform via MQTT
- **Manage** edge device lifecycle, configuration, and software updates
- **Monitor** device health, status, and metrics with real-time reporting
- **Orchestrate** workflows, data collection, and remote operations
- **Integrate** with industrial protocols (Modbus, BACnet, OPC-UA) and application protocols (Serial, D-Bus, SNMP, HTTP, TCP/UDP)
- **Bridge** to cloud services (AWS IoT Core, Azure IoT Hub, GCP, satellite networks)

## Ubuntu Core Deployment Model

### Why Ubuntu Core?

The Coda agent is packaged as a snap and deployed on **Ubuntu Core** - Canonical's minimal, secure, and immutable operating system for IoT devices. This deployment model provides:

1. **Security**: Strict confinement with AppArmor and Seccomp isolation
2. **Reliability**: Transactional updates with automatic rollback on failure
3. **Maintainability**: Read-only root filesystem with atomic snap updates
4. **Longevity**: 10+ years of security updates for LTS releases
5. **Remote Management**: Over-the-air updates and configuration management

### Snap Confinement Model

The Coda snap runs with **strict confinement**, which means:

- The snap application is isolated from the host system
- Access to system resources requires explicit interface connections (plugs)
- Configuration is managed through snapd's configuration system
- Persistent data is stored in controlled, versioned directories

This provides security while still allowing necessary system access through controlled interfaces.

## EdgeIQ Symphony Platform Integration

### Platform Architecture

Coda acts as the bridge between edge devices and the EdgeIQ Symphony cloud platform:

```
[Edge Devices] <--> [Coda Agent] <--> [MQTT Broker] <--> [EdgeIQ Symphony Platform]
                         |
                         v
                  [Local Services]
                  - Data Collection
                  - Protocol Translation
                  - Workflow Execution
                  - Remote Terminal
```

### Key Integration Points

1. **MQTT Communication**
   - Persistent connection to EdgeIQ MQTT broker (mqtt.edgeiq.io)
   - Device registration and authentication
   - Bidirectional command/control messaging
   - Configuration updates via MQTT commands

2. **REST API Integration**
   - Configuration downloads (app_config.zip via HTTP)
   - Software updates and release management
   - Telemetry and metrics reporting
   - Log uploads for diagnostics

3. **Device Identity**
   - Unique device identifier (typically MAC address-based)
   - Company ID for tenant isolation
   - TPM 2.0 support for certificate-based authentication
   - Secure credential storage

## IoT Device Management Capabilities

### Core Features

1. **Device Lifecycle Management**
   - Automated device provisioning and registration
   - Remote configuration management
   - Software updates and version control
   - Health monitoring and diagnostics

2. **Protocol Support**
   - **Industrial Protocols**: Modbus RTU/TCP, BACnet, OPC-UA
   - **Application Protocols**: HTTP, MQTT, TCP/UDP, Serial, D-Bus, SNMP
   - **Network Protocols**: Ethernet, WiFi, cellular (via ModemManager), PPP

3. **Data Collection and Ingestion**
   - Real-time sensor data collection
   - Protocol translation and normalization
   - Local buffering with persistence
   - Configurable relay frequency limits

4. **Remote Operations**
   - Remote terminal access for diagnostics
   - Remote command execution
   - Log collection and upload
   - System reboot/shutdown control

5. **Network Management**
   - Network configuration via NetworkManager (nmcli)
   - WiFi, Ethernet, cellular modem support
   - Firewall configuration (iptables)
   - Static IP, DHCP, and advanced routing

6. **Security Features**
   - TPM 2.0 hardware security module integration
   - Certificate-based authentication
   - Encrypted communication (TLS/SSL)
   - Secure credential storage

### Platform Use Cases

Coda enables a wide range of IoT use cases:

- **Industrial IoT**: Factory automation, equipment monitoring, predictive maintenance
- **Smart Buildings**: HVAC control, energy management, access control
- **Transportation**: Fleet management, vehicle telematics, asset tracking
- **Utilities**: Smart meters, grid monitoring, remote site management
- **Agriculture**: Environmental monitoring, irrigation control, livestock tracking
- **Retail**: Point-of-sale systems, inventory tracking, digital signage

## Architecture Context

### Binary Distribution Model

Unlike traditional snap packages that build from source, the Coda snap:

1. Downloads pre-built Coda binaries from EdgeIQ API during snap build
2. Packages the binary with configuration files and utilities
3. Supports multi-architecture: amd64, arm64, armhf
4. Reduces build time and ensures consistency across platforms

### Configuration Management

The snap uses a sophisticated configuration translation system:

- **Snap Configuration**: Uses dash-separated keys (e.g., `bootstrap.unique-id`)
- **Coda Configuration**: Uses underscore-separated keys (e.g., `bootstrap.unique_id`)
- **Translation Layer**: Hook utilities automatically translate between formats
- **Persistent Storage**: Configuration stored in `$SNAP_COMMON/conf/` (survives updates)

### Hook System

The snap implements three hooks for lifecycle management:

1. **install**: First-time setup, copies default configs, sets MAC-based unique-id
2. **configure**: Handles `snap set` commands, updates configuration files
3. **post-refresh**: Runs after snap updates (currently minimal)

### Snap Interfaces

The Coda snap requires extensive system access via snap interfaces:

- **Network**: MQTT, HTTP, network management, firewall control
- **Device Control**: Shutdown, reboot, snap management
- **Hardware**: TPM, USB, hardware/system observation
- **Monitoring**: Logs, memory, mounts, SSH keys

## Development and Deployment

### Local Development

Development workflow supports:

1. Local snap builds using LXD containers or Multipass VMs
2. E2E testing with real Ubuntu environments and mock EdgeIQ platform
3. Hook development and testing with configuration validation
4. Multi-architecture builds via Launchpad remote build

### Publishing Workflow

Production releases follow this process:

1. Version selection (e.g., EDGEIQ_CODA_VERSION=4.0.22)
2. Remote build on Launchpad for all architectures
3. Testing with E2E test suite
4. Publication to Snap Store (edge/beta/candidate/stable channels)
5. Gradual rollout to production devices

### Testing Infrastructure

Comprehensive testing includes:

- **E2E Tests**: Multipass VM-based testing with real Ubuntu snapd
- **Mock Platform**: Python-based EdgeIQ API and MQTT simulator
- **Hook Tests**: Configuration management and lifecycle validation
- **Integration Tests**: Network management, interface connections, TPM integration

## Repository Structure

```
coda-snap/
├── .agent/                      # This documentation
│   ├── README.md               # This file - overview and context
│   ├── System/                 # Technical architecture documentation
│   ├── SOP/                    # Standard Operating Procedures
│   └── Tasks/                  # Product requirements and planning
├── snap/                       # Snap packaging
│   ├── hooks/                  # Lifecycle hooks (install, configure, post-refresh)
│   └── local/                  # Snapcraft templates
├── utils/                      # Shared utilities
│   └── shared/                 # Hook utilities and configuration translation
├── e2e-tests/                  # End-to-end testing
│   ├── mock-server/           # EdgeIQ platform simulator
│   ├── test-runner/           # Pytest test suite
│   └── fixtures/              # Test data and configurations
├── Makefile                    # Build, test, and deployment automation
├── README.md                   # User-facing documentation
└── CLAUDE.md                   # AI assistant guidance

```

## Key Concepts

### Device Identity

Every Coda device has:

- **Unique ID**: Device-specific identifier (MAC address, serial number, or custom)
- **Company ID**: Tenant identifier for multi-tenancy
- **Device Type**: Defines capabilities and role (gateway vs. endpoint)
- **Authentication**: Password or TPM certificate-based

### Configuration Files

Three primary configuration files:

1. **bootstrap.json**: Initial device configuration (company ID, unique ID, platform URL)
2. **conf.json**: Runtime configuration (MQTT broker, logging, relay settings)
3. **identifier.json**: Device identity (generated from bootstrap config)
4. **app_config.json**: Platform-provided configuration (downloaded via MQTT/HTTP)

### Configuration Flow

1. Device starts with bootstrap.json and conf.json
2. Connects to MQTT broker with credentials
3. Requests app_config via MQTT (v3 protocol)
4. Downloads app_config.zip from platform API
5. Extracts and applies configuration
6. Begins normal operation with full capabilities

## Relationship to EdgeIQ Platform

Coda is one component in the broader EdgeIQ ecosystem:

- **EdgeIQ Symphony**: Cloud platform (SaaS) for device management and orchestration
- **Coda Agent**: Edge runtime (this repository) deployed on customer devices
- **EdgeIQ API**: REST API for configuration, updates, and telemetry
- **MQTT Broker**: Message broker for real-time device communication
- **Web Portal**: User interface for device management and monitoring

This repository focuses specifically on the snap packaging, deployment, and lifecycle management of the Coda agent for Ubuntu Core environments.

## Next Steps

- **System Documentation**: See [System/README.md](System/README.md) for detailed technical architecture
- **Operations**: See [SOP/README.md](SOP/README.md) for build, test, and deployment procedures
- **Development**: See [../CLAUDE.md](../CLAUDE.md) for development guidance and commands
- **Planning**: See [Tasks/README.md](Tasks/README.md) for feature roadmap and tasks

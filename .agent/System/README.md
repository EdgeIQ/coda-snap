# Coda Snap - System Architecture

## Table of Contents

1. [Snap Architecture](#snap-architecture)
2. [Confinement Model](#confinement-model)
3. [Hook System](#hook-system)
4. [Configuration Management](#configuration-management)
5. [Network Configuration](#network-configuration)
6. [TPM 2.0 Integration](#tpm-20-integration)
7. [Snap Interface Connections](#snap-interface-connections)
8. [Build Process](#build-process)
9. [Multi-Architecture Support](#multi-architecture-support)
10. [E2E Testing Architecture](#e2e-testing-architecture)

---

## Snap Architecture

### Overview

The Coda snap packages the EdgeIQ Coda edge agent as a strictly-confined Ubuntu snap. This provides isolation, security, and reliable updates while allowing necessary system access through controlled interfaces.

### Snap Structure

```
coda.snap (installed at /snap/coda/<revision>/)
├── edge                        # Main Coda binary (from EdgeIQ API)
├── conf/                       # Default configuration templates
│   ├── bootstrap.json         # Bootstrap configuration
│   └── conf.json              # Runtime configuration
├── shared/                     # Hook utilities
│   └── hook_utils.py          # Configuration translation utilities
├── bin/                        # System binaries (network-manager, etc.)
└── meta/                       # Snap metadata
    ├── snap.yaml              # Snap manifest
    └── hooks/                 # Lifecycle hooks
        ├── install
        ├── configure
        └── post-refresh
```

### Runtime Directories

**Read-only directories** (immutable):
- `/snap/coda/current/` - Snap files (read-only, symlink to current revision)
- `/snap/coda/<revision>/` - Specific snap revision

**Writable directories** (persistent across updates):
- `/var/snap/coda/common/` - Persistent data (`$SNAP_COMMON`)
  - `conf/` - Configuration files (bootstrap.json, conf.json, identifier.json)
  - `data/` - Application data
  - `logs/` - Log files
- `/var/snap/coda/current/` - Current revision data (`$SNAP_DATA`)
- `/var/snap/coda/<revision>/` - Revision-specific data

### Application Definition

```yaml
apps:
  agent:
    command: edge                    # Run the Coda edge binary
    daemon: simple                   # systemd simple daemon
    restart-condition: always        # Auto-restart on failure
    plugs:                          # Required interfaces (see Snap Interfaces section)
      - home
      - shutdown
      - snapd-control
      # ... (30+ interfaces)
```

The `agent` app runs as a systemd service: `snap.coda.agent.service`

---

## Confinement Model

### Strict Confinement

The Coda snap uses **strict confinement**, providing maximum security through:

1. **AppArmor**: MAC (Mandatory Access Control) policy enforcement
2. **Seccomp**: System call filtering
3. **Namespace isolation**: Process, mount, network isolation
4. **Device access control**: Controlled via interfaces

### Security Boundaries

**What the snap CANNOT do (without interface connections):**
- Access files outside snap directories
- Bind to privileged ports (<1024)
- Access hardware devices
- Manage system services
- Modify network configuration
- Reboot the system

**What the snap CAN do (with interface connections):**
- Network communication (MQTT, HTTP)
- Read/write persistent data in `/var/snap/coda/common/`
- Execute the Coda binary with configured parameters
- Log to syslog via journald

### Interface-Based Permission Model

Permissions are granted by connecting snap interfaces (plugs):

```bash
# Example: Grant shutdown permission
sudo snap connect coda:shutdown :shutdown

# Example: Grant network management permission
sudo snap connect coda:network-control :network-control
```

Each interface connection is audited and can be disconnected to revoke access.

---

## Hook System

### Overview

Snap hooks are executable scripts that run at specific lifecycle events. The Coda snap implements three hooks in Python.

### Hook Architecture

```
snap/hooks/
├── install        # Run once on first installation
├── configure      # Run on every "snap set" command
└── post-refresh   # Run after snap updates
```

All hooks:
- Are written in Python 3
- Use shared utilities from `utils/shared/hook_utils.py`
- Log to journald with specific tags (e.g., `coda.hook.install`)
- Have network access via the `plugs: [network]` declaration

### Install Hook

**File**: `snap/hooks/install`

**Purpose**: First-time device setup

**Execution**: Runs once during `snap install coda`

**Actions**:
1. Copy default configuration files from `$SNAP/conf/` to `$SNAP_COMMON/conf/`
2. Detect MAC address of first Ethernet interface
3. Set `unique_id` to MAC address (failsafe with retries)
4. Initialize snap configuration with bootstrap.json values
5. Initialize snap configuration with conf.json values

**Code Flow**:
```python
# 1. Copy configuration files
src_conf_dir = os.path.join(os.environ['SNAP'], 'conf')
dst_config_dir = os.path.join(os.environ['SNAP_COMMON'], 'conf')
hook_utils.copy_configuration_files(src_conf_dir, dst_config_dir)

# 2. Get MAC address
unique_id = hook_utils.get_mac_of_first_ethernet_failsafe()

# 3. Load and translate bootstrap config
coda_config = hook_utils.load_json('bootstrap.json')
coda_config['unique_id'] = unique_id
snap_config = hook_utils.translate_config_coda_to_snap(coda_config)

# 4. Set snap configuration
hook_utils.snapctl_set('bootstrap', snap_config)
```

**Environment Variables**:
- `$SNAP`: Read-only snap directory (e.g., `/snap/coda/x1`)
- `$SNAP_COMMON`: Persistent writable directory (`/var/snap/coda/common/`)

**Logging**:
```bash
# View install hook logs
journalctl -t coda.hook.install
```

### Configure Hook

**File**: `snap/hooks/configure`

**Purpose**: Apply configuration changes

**Execution**: Runs on:
- `snap set coda <key>=<value>` commands
- Snap installation (after install hook)
- Snap refresh (after post-refresh hook)

**Actions**:
1. Retrieve current snap configuration from snapd
2. Translate keys from snap format (dashes) to Coda format (underscores)
3. Handle `identifier.json` generation for bootstrap config
4. Write updated configuration files to `$SNAP_COMMON/conf/`
5. Trigger service restart (automatic by snapd)

**Code Flow**:
```python
# 1. Get snap configuration
snap_config_str = hook_utils.snapctl_get('bootstrap')
snap_config_json = json.loads(snap_config_str)

# 2. Translate to Coda format
coda_config = hook_utils.translate_config_snap_to_coda(snap_config_json)

# 3. Handle identifier.json creation
if coda_config.get('company_id') and coda_config.get('unique_id'):
    identifier_data = {
        'company_id': company_id,
        'unique_id': unique_id
    }
    identifier_filepath = os.path.join(config_dir, 'identifier.json')
    hook_utils.save_json(identifier_filepath, identifier_data)
    coda_config['identifier_filepath'] = identifier_filepath

# 4. Save updated configuration
hook_utils.save_json(file_path, coda_config)
```

**Configuration Keys**:

Snap keys use dashes; Coda uses underscores:
- `bootstrap.unique-id` → `bootstrap.unique_id`
- `conf.mqtt.broker.host` → `conf.mqtt.broker.host`

**Logging**:
```bash
# View configure hook logs
journalctl -t coda.hook.configure
```

### Post-Refresh Hook

**File**: `snap/hooks/post-refresh`

**Purpose**: Handle snap updates

**Execution**: Runs after `snap refresh coda`

**Current Implementation**: Minimal (network plug declared, but no custom logic)

**Future Use Cases**:
- Database migrations
- Configuration format updates
- Cleanup of deprecated files
- Version-specific upgrade logic

---

## Configuration Management

### Configuration Files

#### 1. bootstrap.json

**Location**: `$SNAP_COMMON/conf/bootstrap.json`

**Purpose**: Device identity and platform connection

**Key Fields**:
```json
{
  "company_id": "test-company-001",
  "unique_id": "00:11:22:33:44:55",
  "identifier_filepath": "/var/snap/coda/common/conf/identifier.json",
  "network_configurer": "nmcli"
}
```

**Field Descriptions**:
- `company_id`: Tenant identifier (required)
- `unique_id`: Device-specific identifier (required, auto-set to MAC on install)
- `identifier_filepath`: Path to identifier.json (auto-generated by configure hook)
- `network_configurer`: Network management tool (always "nmcli" on Ubuntu Core)

#### 2. conf.json

**Location**: `$SNAP_COMMON/conf/conf.json`

**Purpose**: Runtime configuration (MQTT, platform, logging)

**Key Fields**:
```json
{
  "mqtt": {
    "broker": {
      "protocol": "tcp",
      "host": "mqtt.edgeiq.io",
      "port": 1883,
      "password": "encrypted_password_here"
    }
  },
  "platform": {
    "url": "https://api.edgeiq.io/api/v1/platform"
  },
  "edge": {
    "relay_frequency_limit": 10
  }
}
```

**Field Descriptions**:
- `mqtt.broker.protocol`: Protocol (tcp, ssl, ws, wss)
- `mqtt.broker.host`: MQTT broker hostname
- `mqtt.broker.port`: MQTT broker port
- `mqtt.broker.password`: Encrypted MQTT password
- `platform.url`: EdgeIQ platform API base URL
- `edge.relay_frequency_limit`: Max reports per period

#### 3. identifier.json

**Location**: `$SNAP_COMMON/conf/identifier.json`

**Purpose**: Device identity (auto-generated from bootstrap.json)

**Content**:
```json
{
  "company_id": "test-company-001",
  "unique_id": "00:11:22:33:44:55"
}
```

**Generation**: Created automatically by configure hook when both company_id and unique_id are set

#### 4. app_config.json

**Location**: `$SNAP_COMMON/conf/app_config.json`

**Purpose**: Platform-provided configuration (downloaded at runtime)

**Content**: Complete device, workflow, and integration configuration from EdgeIQ Symphony

**Download Flow**:
1. Device connects to MQTT broker
2. Publishes config request: `u/{company_id}/{unique_id}/config`
3. Platform responds with download URL: `d/{company_id}/{unique_id}/gateway_commands/send_config_v3`
4. Device downloads app_config.zip via HTTP
5. Extracts and applies configuration

### Configuration Translation System

#### Key Format Translation

**Problem**: Snapd configuration keys cannot contain underscores, but Coda uses underscores in JSON.

**Solution**: Automatic bidirectional translation in hook utilities.

#### Translation Functions

```python
# Coda (underscore) → Snap (dash)
def translate_config_coda_to_snap(obj):
    return translate_config(obj, lambda k: k.replace("_", "-"))

# Snap (dash) → Coda (underscore)
def translate_config_snap_to_coda(obj):
    return translate_config(obj, lambda k: k.replace("-", "_"))

# Recursive translation
def translate_config(obj, translation_func):
    if isinstance(obj, dict):
        return {translation_func(k): translate_config(v, translation_func)
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [translate_config(i, translation_func) for i in obj]
    else:
        return obj
```

#### Example Translation

**Coda format** (in JSON files):
```json
{
  "unique_id": "device-001",
  "mqtt": {
    "broker": {
      "host": "mqtt.edgeiq.io"
    }
  }
}
```

**Snap format** (in snapd configuration):
```json
{
  "unique-id": "device-001",
  "mqtt": {
    "broker": {
      "host": "mqtt.edgeiq.io"
    }
  }
}
```

**User Command**:
```bash
# User sets with dashes
sudo snap set coda bootstrap.unique-id=device-001

# Hook translates and writes to bootstrap.json with underscores
# Result in JSON: "unique_id": "device-001"
```

### Configuration Workflow

```
User Command                Hook Processing                File System
┌──────────────────┐       ┌──────────────────┐          ┌──────────────────┐
│ snap set coda    │       │ 1. snapctl get   │          │ Read from:       │
│ bootstrap.       │──────>│    "bootstrap"   │─────────>│ snapd config DB  │
│ unique-id=dev001 │       │                  │          └──────────────────┘
└──────────────────┘       │ 2. Translate     │
                           │    dash → under  │
                           │                  │          ┌──────────────────┐
                           │ 3. Write JSON    │─────────>│ Write to:        │
                           │                  │          │ $SNAP_COMMON/    │
                           │ 4. Restart svc   │          │ conf/bootstrap.  │
                           │    (automatic)   │          │ json             │
                           └──────────────────┘          └──────────────────┘
```

---

## Network Configuration

### NetworkManager Integration

The Coda snap uses **NetworkManager (nmcli)** for network configuration on Ubuntu Core devices.

**Configuration**:
```json
{
  "network_configurer": "nmcli"
}
```

This is set automatically in the `coda` part of snapcraft.yaml:
```bash
jq '.network_configurer = "nmcli"' $SNAPCRAFT_PART_INSTALL/conf/bootstrap.json
```

### Network Interfaces Required

To enable network management capabilities:

```bash
# Core networking
sudo snap connect coda:network :network
sudo snap connect coda:network-bind :network-bind
sudo snap connect coda:network-observe :network-observe

# Network configuration
sudo snap connect coda:network-control :network-control
sudo snap connect coda:network-manager :network-manager
sudo snap connect coda:network-manager-observe :network-manager-observe

# Advanced networking
sudo snap connect coda:network-setup-control :network-setup-control
sudo snap connect coda:network-setup-observe :network-setup-observe
sudo snap connect coda:network-status :network-status

# Firewall
sudo snap connect coda:firewall-control :firewall-control
```

### Network Management Capabilities

With interfaces connected, Coda can:

1. **Configure Network Interfaces**
   - Set static IP addresses
   - Configure DHCP
   - Manage WiFi connections
   - Configure VLANs

2. **Manage Connections**
   - Create/modify NetworkManager connections
   - Enable/disable interfaces
   - Set connection priorities

3. **Firewall Management**
   - Configure iptables rules
   - Set up NAT/masquerading
   - Port forwarding

4. **Modem Management** (future)
   - Cellular modem configuration
   - PPP connections
   - APN settings

### Network Configuration API

EdgeIQ provides a [Network Configuration API](https://dev.edgeiq.io/docs/network-configuration) that allows:

- Remote network configuration from Symphony platform
- API-driven interface setup
- Automated network provisioning

**Example Use Case**: Configure device network remotely via EdgeIQ API → Platform sends MQTT command → Coda executes nmcli commands → Network reconfigured

---

## TPM 2.0 Integration

### Overview

TPM (Trusted Platform Module) 2.0 provides hardware-based security for certificate-based device authentication.

### Purpose

1. **Secure Key Storage**: Private keys stored in TPM hardware (cannot be extracted)
2. **Certificate-Based Auth**: Use X.509 certificates instead of passwords
3. **Hardware Identity**: TPM endorsement key provides unique device identity
4. **Attestation**: Cryptographic proof of device integrity

### Enabling TPM Support

**Connect the TPM interface**:
```bash
sudo snap connect coda:tpm :tpm
```

**Configure Coda for TPM**:
Follow EdgeIQ documentation: [Configuring Edge Devices with TPM Support for Enhanced Security](https://dev.edgeiq.io/docs/configuring-edge-devices-with-tpm-support-for-enhanced-security)

### TPM Workflow

1. **Certificate Provisioning**
   - Generate or import device certificate
   - Store private key in TPM
   - Upload certificate to EdgeIQ platform

2. **Authentication**
   - Coda uses TPM-stored private key
   - Signs authentication challenge
   - Platform verifies with public certificate

3. **Secure Communication**
   - TLS mutual authentication (mTLS)
   - TPM-backed private key for signing
   - Stronger security than password-based auth

### Benefits

- **Tamper-Resistant**: Private keys cannot be extracted from TPM
- **Unique Identity**: Each TPM has unique endorsement key
- **Regulatory Compliance**: Meets security standards for critical infrastructure
- **Zero-Touch Provisioning**: Automated device onboarding with certificates

---

## Snap Interface Connections

### Overview

Snap interfaces are the security mechanism for granting system access. Each interface must be explicitly connected.

### Core Interfaces

#### System Control

| Interface | Plug | Purpose | Risk Level |
|-----------|------|---------|------------|
| `shutdown` | `coda:shutdown` | Reboot/shutdown device | High |
| `snapd-control` | `coda:snapd-control` | Manage other snaps | High |

**Use Case**: Remote device reboot, snap installation/updates

```bash
sudo snap connect coda:shutdown :shutdown
sudo snap connect coda:snapd-control :snapd-control
```

#### Networking

| Interface | Plug | Purpose | Risk Level |
|-----------|------|---------|------------|
| `network` | `coda:network` | Network access | Low |
| `network-bind` | `coda:network-bind` | Bind to ports | Low |
| `network-control` | `coda:network-control` | Configure networking | High |
| `network-manager` | `coda:network-manager` | NetworkManager control | High |
| `firewall-control` | `coda:firewall-control` | Firewall configuration | High |

**Use Case**: MQTT communication, network configuration, firewall management

#### Hardware Access

| Interface | Plug | Purpose | Risk Level |
|-----------|------|---------|------------|
| `tpm` | `coda:tpm` | TPM 2.0 access | Medium |
| `raw-usb` | `coda:raw-usb` | Direct USB access | High |

**Use Case**: Certificate-based auth (TPM), USB device communication

#### System Observation

| Interface | Plug | Purpose | Risk Level |
|-----------|------|---------|------------|
| `hardware-observe` | `coda:hardware-observe` | Read hardware info | Low |
| `system-observe` | `coda:system-observe` | Read system info | Low |
| `log-observe` | `coda:log-observe` | Read system logs | Medium |
| `mount-observe` | `coda:mount-observe` | Read mount info | Low |

**Use Case**: Device monitoring, telemetry, diagnostics

#### Modem/Cellular (Future)

| Interface | Plug | Purpose | Risk Level |
|-----------|------|---------|------------|
| `modem-manager` | `coda:modem-manager` | Cellular modem control | High |
| `ppp` | `coda:ppp` | PPP connections | Medium |

**Status**: Declared but not yet fully supported

### Auto-Connection

Most interfaces require manual connection by the user or device administrator. Some interfaces may be auto-connected if the snap store grants the permission (requires manual review).

### Interface Connection Script

For automated setup:

```bash
#!/bin/bash
# connect-interfaces.sh - Connect all Coda interfaces

INTERFACES=(
    "home"
    "shutdown"
    "snapd-control"
    "hardware-observe"
    "system-observe"
    "network"
    "network-bind"
    "network-control"
    "network-manager"
    "network-manager-observe"
    "network-observe"
    "network-setup-control"
    "network-setup-observe"
    "network-status"
    "modem-manager"
    "ppp"
    "firewall-control"
    "tpm"
    "log-observe"
    "physical-memory-observe"
    "mount-observe"
    "ssh-public-keys"
    "raw-usb"
)

for iface in "${INTERFACES[@]}"; do
    echo "Connecting coda:$iface"
    sudo snap connect "coda:$iface" ":$iface" 2>/dev/null || \
        echo "  ⚠ Could not connect $iface (may not be available)"
done

echo "✓ Interface connections complete"
```

---

## Build Process

### Overview

The Coda snap uses a **binary distribution model** where pre-built Coda binaries are downloaded from the EdgeIQ API during the snap build process.

### Snapcraft Parts

#### Part 1: deps

```yaml
deps:
  plugin: nil
  stage-packages:
    - network-manager      # nmcli command
    - modemmanager        # Cellular modem support
    - iptables            # Firewall management
    - iputils-ping        # Network diagnostics
```

Installs system dependencies into the snap.

#### Part 2: utils

```yaml
utils:
  plugin: dump
  source: utils
```

Copies Python utilities (hook_utils.py) into the snap.

#### Part 3: coda

```yaml
coda:
  plugin: nil
  build-packages:
    - wget
    - jq
  override-build: |
    # Download configuration templates
    wget $EDGEIQ_API_URL/api/v1/platform/releases/$VERSION/edge-assets-$VERSION.tar.gz
    tar -xvf edge-assets.tar.gz

    # Set network_configurer to nmcli
    jq '.network_configurer = "nmcli"' conf/bootstrap.json > conf/temp.json
    mv conf/temp.json conf/bootstrap.json

    # Download architecture-specific binary
    wget $EDGEIQ_API_URL/api/v1/platform/releases/$VERSION/edge-linux-$ARCH-$VERSION -O edge
    chmod +x edge
```

Downloads and packages the Coda binary and configuration templates.

### Architecture Detection

Architecture mapping during build:

```bash
case $SNAPCRAFT_ARCH_TRIPLET in
  "x86_64-linux-gnu")      ARCH=amd64 ;;
  "arm-linux-gnueabihf")   ARCH=arm7  ;;
  "aarch64-linux-gnu")     ARCH=arm64 ;;
esac
```

### Build Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `EDGEIQ_SNAP_NAME` | Snap name | `coda` |
| `EDGEIQ_API_URL` | EdgeIQ API base URL | `https://api.edgeiq.io` |
| `EDGEIQ_CODA_VERSION` | Coda version to package | `4.0.22` |
| `EDGEIQ_CODA_SNAP_VERSION` | Snap version (dashes) | `4.0.22` |

### Template Processing

The `snapcraft.yaml` is generated from a template:

```bash
make template
# Generates snap/snapcraft.yaml from snap/local/snapcraft.template.yaml
# Substitutes {{EDGEIQ_CODA_VERSION}}, {{EDGEIQ_API_URL}}, etc.
```

### Build Commands

**Local build (with LXD)**:
```bash
export EDGEIQ_CODA_VERSION=4.0.22
make clean build
# Result: coda_4.0.22_amd64.snap
```

**Local build (Multipass VM)**:
```bash
export EDGEIQ_CODA_VERSION=4.0.22
make build-local
# Builds in VM, transfers snap to host
```

**Remote build (Launchpad - all architectures)**:
```bash
export EDGEIQ_CODA_VERSION=4.0.22
make template
snapcraft remote-build --launchpad-accept-public-upload --launchpad-timeout 3600 --build-for=amd64,armhf,arm64
# Result: coda_4.0.22_amd64.snap, coda_4.0.22_armhf.snap, coda_4.0.22_arm64.snap
```

### Build Output

Snap files are named: `{name}_{version}_{arch}.snap`

Example: `coda_4.0.22_amd64.snap`

---

## Multi-Architecture Support

### Supported Architectures

| Architecture | Description | Devices |
|--------------|-------------|---------|
| `amd64` (x86_64) | Intel/AMD 64-bit | Industrial PCs, servers, VMs |
| `arm64` (aarch64) | ARM 64-bit | Raspberry Pi 4, NVIDIA Jetson, modern ARM devices |
| `armhf` (arm7) | ARM 32-bit | Raspberry Pi 2/3, older ARM devices |

### Architecture-Specific Binary Download

During build, the correct binary is downloaded:

```bash
# amd64 build
wget $API/releases/$VERSION/edge-linux-amd64-$VERSION -O edge

# arm64 build
wget $API/releases/$VERSION/edge-linux-arm64-$VERSION -O edge

# armhf build
wget $API/releases/$VERSION/edge-linux-arm7-$VERSION -O edge
```

### Remote Build Process

Launchpad builds all architectures in parallel:

```bash
snapcraft remote-build --build-for=amd64,armhf,arm64
```

**Workflow**:
1. Upload source to Launchpad
2. Create build jobs for each architecture
3. Build in native environments (not cross-compilation)
4. Download completed snaps

**Timeout**: Default 1 hour (configurable with `--launchpad-timeout`)

### Testing Multi-Architecture

E2E tests run on Ubuntu 24.04 (amd64), but snaps can be tested on:

- **amd64**: Ubuntu Core VM/physical device
- **arm64**: Raspberry Pi 4 with Ubuntu Core
- **armhf**: Raspberry Pi 2/3 with Ubuntu Core

---

## E2E Testing Architecture

### Overview

The E2E test suite uses **Multipass VMs** with real Ubuntu 24.04 environments for authentic snap testing, providing more accurate validation than containerized environments.

### Test Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│ Host Machine (macOS/Linux/Windows)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Test Runner (pytest)                                │  │
│  │ - Executes tests via multipass exec                 │  │
│  │ - Validates snap behavior                           │  │
│  │ - Reports results                                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼ multipass exec                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Multipass VM (coda-test-vm)                         │  │
│  │ - Ubuntu 24.04 LTS                                  │  │
│  │ - 2 CPUs, 2GB RAM, 10GB disk                        │  │
│  │ - Native snapd                                      │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ Coda Snap (Under Test)                      │  │  │
│  │  │ - Installed from local .snap file           │  │  │
│  │  │ - Configured with test credentials          │  │  │
│  │  │ - Connected to local mock services          │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ Mock EdgeIQ Server (Python)                 │  │  │
│  │  │ - HTTP API (port 8080)                      │  │  │
│  │  │   - /health endpoint                        │  │  │
│  │  │   - /api/v1/platform/configs_v3/...        │  │  │
│  │  │ - MQTT Client (connects to Mosquitto)      │  │  │
│  │  │   - Subscribes to u/+/+/config             │  │  │
│  │  │   - Publishes to d/.../send_config_v3      │  │  │
│  │  │ - systemd service                          │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ Mosquitto MQTT Broker                       │  │  │
│  │  │ - Port 1883                                 │  │  │
│  │  │ - Anonymous auth enabled                    │  │  │
│  │  │ - Message bridge                            │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Multipass VM Configuration

**VM Specifications**:
- **Image**: Ubuntu 24.04 LTS
- **CPUs**: 2
- **Memory**: 2GB
- **Disk**: 10GB
- **Network**: Bridged (host-accessible)

**Cloud-Init Setup** (`e2e-tests/cloud-init.yaml`):
```yaml
#cloud-config
package_update: true
package_upgrade: true
packages:
  - python3
  - python3-pip
  - mosquitto
  - mosquitto-clients
```

### Mock EdgeIQ Server

**File**: `e2e-tests/mock-server/server.py`

**Purpose**: Simulates EdgeIQ Symphony platform

**Components**:

1. **HTTP Server** (aiohttp)
   - Health check: `GET /health`
   - Config download: `GET /api/v1/platform/configs_v3/{company_id}/{device_id}/app_config.zip`
   - Returns zip file with app_config.json

2. **MQTT Client** (paho-mqtt)
   - Connects to Mosquitto broker
   - Subscribes to: `u/+/+/config` (device config requests)
   - Publishes to: `d/{company_id}/{device_id}/gateway_commands/send_config_v3`
   - Sends config download URL and MD5 hash

3. **Configuration Generation**
   - Generates app_config.json dynamically
   - Creates zip file in memory
   - Computes MD5 hash for validation

**Systemd Service**:
- Unit file: `e2e-tests/mock-server/edgeiq-mock-server.service`
- Runs as systemd service in VM
- Logs to journald

### Test Suite

**File**: `e2e-tests/test-runner/tests/test_coda_snap.py`

**Test Class**: `TestCodaSnapInstallation`

**Key Tests**:

1. **test_install_coda_snap**
   - Install snap from local file or store
   - Connect required interfaces
   - Configure device identity
   - Configure MQTT connection
   - Verify configuration applied
   - Check snap logs

2. **test_disk_space_exhaustion_crash**
   - Create small loop device (10MB)
   - Mount over common directory
   - Fill disk to capacity
   - Monitor snap behavior
   - Verify graceful handling (no crashes)
   - Cleanup and restore

**Test Execution**:
```python
# Execute command in VM
def exec_command(vm_name, command, check=True, timeout=300):
    result = subprocess.run(
        ['multipass', 'exec', vm_name, '--', 'bash', '-c', command],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result.returncode, result.stdout + result.stderr
```

### Test Fixtures

**File**: `e2e-tests/test-runner/tests/conftest.py`

**Fixtures**:

1. **multipass_vm**
   - Provides VM name
   - Ensures VM exists and is running

2. **wait_for_services**
   - Waits for mock server to be ready
   - Waits for Mosquitto to be ready
   - Timeout with retries

3. **snap_in_vm**
   - Determines snap source (local file vs. store)
   - Transfers local snap to VM if needed
   - Returns snap installation parameters

### Test Workflow

**Full E2E Test** (`make e2e-test`):
```bash
1. Cleanup: Delete existing VM (if any)
2. Create VM: Launch Ubuntu 24.04 VM with cloud-init
3. Wait: Ensure snapd is ready
4. Setup: Install and start mock services
5. Test: Run pytest test suite
6. Cleanup: Delete VM
7. Report: Show results
```

**Interactive Workflow**:
```bash
# Step-by-step for debugging
make e2e-test-setup      # Create VM and services
make e2e-test-run        # Run tests (VM kept running)
make vm-shell            # Access VM for debugging
make e2e-test-clean      # Cleanup when done
```

### Test Commands

```bash
# Full automated test
make e2e-test

# Setup test environment
make e2e-test-setup

# Run tests (requires setup first)
make e2e-test-run

# Check VM and service status
make e2e-test-check
make e2e-test-status

# View logs
make e2e-test-logs              # Follow logs
make vm-services-logs           # Last 50 lines

# Debugging
make vm-shell                   # SSH into VM
make vm-info                    # VM details
make vm-list                    # All VMs

# Cleanup
make e2e-test-clean             # Delete VM and artifacts
```

### Local Snap Testing

Test a locally-built snap:

```bash
# 1. Build snap
export EDGEIQ_CODA_VERSION=4.0.22
make build-local

# 2. Run E2E tests with local snap
CODA_SNAP_FILE=./coda_4.0.22_amd64.snap make e2e-test-run
```

The test suite automatically detects the local snap file and uses it instead of installing from the store.

### Test Output

**Success Example**:
```
============ E2E Test Suite ============
✓ VM created: coda-test-vm
✓ Services ready
✓ Snap installed
✓ Configuration applied
✓ Coda agent running
✓ All tests passed
============ Cleanup Complete ===========
```

**Failure Example**:
```
============ E2E Test Suite ============
✓ VM created: coda-test-vm
✓ Services ready
✗ Snap installation failed
  Error: snap not found in store
  Logs: /tmp/test-logs.txt
============ Cleanup Complete ===========
```

---

## Summary

The Coda snap architecture provides:

1. **Security**: Strict confinement with controlled interfaces
2. **Reliability**: Transactional updates with automatic rollback
3. **Flexibility**: Extensive system access through 30+ interfaces
4. **Portability**: Multi-architecture support (amd64, arm64, armhf)
5. **Testability**: Comprehensive E2E testing with Multipass VMs
6. **Maintainability**: Configuration translation system, lifecycle hooks

This architecture enables EdgeIQ to deliver secure, reliable edge agents at scale across diverse IoT deployments.

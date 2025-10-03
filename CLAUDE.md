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

### Hook Utilities

Common functionality in `utils/shared/hook_utils.py`:

- **Key Translation**: Snap uses dashes (e.g., `relay-frequency-limit`) while Coda uses underscores (e.g., `relay_frequency_limit`)
- **MAC Address Detection**: `get_mac_of_first_ethernet_failsafe()` with 3 retry attempts
- **Configuration Management**: JSON loading/saving with snapctl integration
- **Config Translation**: Recursive translation between snap and Coda key formats

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

## Key Architectural Points

1. **Binary Distribution Model**: The snap doesn't build Coda from source; it downloads pre-built binaries from EdgeIQ API
2. **Configuration Translation Layer**: Snap hook utilities translate between snap's dash-based keys and Coda's underscore-based keys
3. **Network Manager Integration**: Bootstrap config is modified during build to use "nmcli" for network configuration on Ubuntu Core
4. **Multi-Architecture Support**: Single codebase builds for amd64, arm64, and armhf with architecture-specific binary downloads
5. **Persistent Configuration**: All runtime config stored in `$SNAP_COMMON/conf/` which persists across snap updates

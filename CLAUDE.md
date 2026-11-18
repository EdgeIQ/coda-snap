# CLAUDE.md - Coda Snap Development Guide

This file provides guidance to Claude Code (claude.ai/code) when working with the coda-snap repository.

## Repository Overview

This repository contains the **Coda Snap** - EdgeIQ's edge agent packaged as an Ubuntu Core snap. This is THE device agent that runs on edge devices to connect them to the EdgeIQ Symphony platform.

**Key Characteristics**:
- Strictly-confined Ubuntu snap for security
- Multi-architecture support (amd64, arm64, armhf)
- Binary distribution model (downloads pre-built Coda from EdgeIQ API)
- Comprehensive hook system for configuration management
- E2E testing with Multipass VMs

## Documentation Structure

This repository uses the `.agent/` documentation methodology:

- **[.agent/README.md](.agent/README.md)**: Overview, context, and platform integration
- **[.agent/System/README.md](.agent/System/README.md)**: Technical architecture and system design
- **[.agent/SOP/README.md](.agent/SOP/README.md)**: Standard Operating Procedures for build/test/deploy
- **[.agent/Tasks/README.md](.agent/Tasks/README.md)**: Feature roadmap and task planning
- **This file (CLAUDE.md)**: Development commands and quick reference

**When to use what**:
- Need to understand snap architecture? → `.agent/System/README.md`
- Need to build or publish? → `.agent/SOP/README.md`
- Planning new features? → `.agent/Tasks/README.md`
- Quick command reference? → This file

## Quick Start

### First Time Setup

```bash
# Install prerequisites (Ubuntu)
sudo snap install snapcraft --classic
sudo snap install lxd
sudo lxd init --auto

# Install prerequisites (macOS)
brew install multipass

# Clone repository and explore
cd coda-snap
ls -la
```

### Build and Test Workflow

```bash
# 1. Set version
export EDGEIQ_CODA_VERSION=4.0.22

# 2. Build snap locally
make build-local

# 3. Run E2E tests
CODA_SNAP_FILE=./coda_4.0.22_amd64.snap make e2e-test

# 4. If tests pass, ready for publishing
```

## Makefile Targets

### Build Targets

| Target | Description | Use Case |
|--------|-------------|----------|
| `make setup` | Install snapcraft and LXD | First-time setup on Ubuntu |
| `make template` | Generate snapcraft.yaml from template | Before building |
| `make build` | Build snap with LXD | Local development (Ubuntu) |
| `make build-local` | Build snap in Multipass VM | Local development (macOS/Windows) |
| `make clean` | Clean build artifacts | Before fresh build |

**Example - Local Build**:
```bash
export EDGEIQ_CODA_VERSION=4.0.22
make clean build
```

**Example - Multipass Build**:
```bash
export EDGEIQ_CODA_VERSION=4.0.22
make build-local
```

### Installation Targets

| Target | Description | Use Case |
|--------|-------------|----------|
| `make install` | Install snap locally | Testing on Ubuntu device |
| `make uninstall` | Remove snap | Cleanup |
| `make connect` | Connect all snap interfaces | After installation |

### E2E Testing Targets

| Target | Description | Use Case |
|--------|-------------|----------|
| `make e2e-test` | Full test suite (create VM → test → cleanup) | Automated testing |
| `make e2e-test-setup` | Create VM and services | Interactive testing |
| `make e2e-test-run` | Run tests (requires setup) | Re-run tests |
| `make e2e-test-clean` | Delete VM and cleanup | After testing |
| `make e2e-test-check` | Check VM and service status | Diagnostics |
| `make e2e-test-status` | Detailed status report | Debugging |
| `make e2e-test-logs` | Follow service logs | Real-time monitoring |

### VM Management Targets

| Target | Description | Use Case |
|--------|-------------|----------|
| `make vm-shell` | Open shell in VM | Debugging |
| `make vm-info` | Show VM details | Diagnostics |
| `make vm-list` | List all VMs | Overview |

### Publishing Targets

| Target | Description | Use Case |
|--------|-------------|----------|
| `make login` | Export Snapcraft credentials | First-time publisher setup |
| `make remote-build` | Build all architectures on Launchpad | Production builds |
| `make publish` | Upload and publish to store | Releasing |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EDGEIQ_CODA_VERSION` | `latest` | Coda version to package |
| `EDGEIQ_SNAP_NAME` | `coda` | Snap name |
| `EDGEIQ_API_URL` | `https://api.edgeiq.io` | EdgeIQ API base URL |
| `SNAPCRAFT_CHANNEL` | `edge,beta,candidate,stable` | Publishing channels |
| `MULTIPASS_VM_NAME` | `coda-test-vm` | VM name for E2E tests |
| `CODA_SNAP_FILE` | (none) | Local snap file for E2E tests |

## Development Workflows

### Workflow 1: Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/improve-hooks

# 2. Make code changes
vim snap/hooks/configure

# 3. Build and test locally
export EDGEIQ_CODA_VERSION=4.0.22
make build-local

# 4. Run E2E tests
CODA_SNAP_FILE=./coda_4.0.22_amd64.snap make e2e-test

# 5. Commit and push
git add snap/hooks/configure
git commit -m "feat: improve configuration hook error handling"
git push origin feature/improve-hooks
```

### Workflow 2: Version Update

```bash
# 1. Identify new version
export EDGEIQ_CODA_VERSION=4.1.0

# 2. Test build locally
make build-local

# 3. Run E2E tests
CODA_SNAP_FILE=./coda_4.1.0_amd64.snap make e2e-test

# 4. If tests pass, remote build
make template
snapcraft remote-build --build-for=amd64,armhf,arm64

# 5. Publish to edge channel
export SNAPCRAFT_CHANNEL="edge"
make publish
```

### Workflow 3: Hook Development

```bash
# 1. Make hook changes
vim snap/hooks/configure

# 2. Build snap
make build-local

# 3. Test in VM
make e2e-test-setup
make vm-shell

# Inside VM:
sudo snap install --dangerous /home/ubuntu/coda_*.snap
journalctl -t coda.hook.install
sudo snap set coda bootstrap.unique-id=test-123
journalctl -t coda.hook.configure
exit

# 4. Run full E2E tests
make e2e-test-run
make e2e-test-clean
```

## Common Development Issues

### LXD Build Fails

**Solutions**:
```bash
# Reinitialize LXD
sudo lxd init --auto

# Or use Multipass
make build-local
```

### E2E Tests Fail

**Solutions**:
```bash
# Check VM and services
make e2e-test-check
make vm-shell

# Inside VM:
snap list
sudo snap logs coda
sudo systemctl status edgeiq-mock-server
```

### Hook Fails

**Solutions**:
```bash
# View hook logs
journalctl -t coda.hook.configure -n 100 --no-pager

# Reinstall snap
sudo snap remove coda
sudo snap install --dangerous coda_*.snap
```

## Best Practices

### DO:
- ✅ Read `.agent/` documentation before making changes
- ✅ Run E2E tests before committing
- ✅ Update documentation with code changes
- ✅ Use `make template` before building
- ✅ Follow conventional commits

### DON'T:
- ❌ Edit `snap/snapcraft.yaml` directly (use template)
- ❌ Skip E2E tests
- ❌ Publish directly to stable
- ❌ Hardcode version numbers

## Related Resources

### Documentation
- [.agent/README.md](.agent/README.md) - Overview and context
- [.agent/System/README.md](.agent/System/README.md) - Technical architecture
- [.agent/SOP/README.md](.agent/SOP/README.md) - Operating procedures
- [.agent/Tasks/README.md](.agent/Tasks/README.md) - Feature roadmap
- [README.md](README.md) - User-facing documentation

### External Resources
- [Snapcraft Documentation](https://snapcraft.io/docs)
- [Ubuntu Core Documentation](https://ubuntu.com/core/docs)
- [EdgeIQ Developer Portal](https://dev.edgeiq.io/)

---

**Note**: When making structural or architectural changes to the codebase, always update the relevant documentation files (AGENTS.md, README.md, and `.agent/` docs).

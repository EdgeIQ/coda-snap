# Coda Snap - Task Planning and Feature Roadmap

This document tracks planned features, enhancements, and technical debt for the Coda snap package.

## Table of Contents

1. [Active Features](#active-features)
2. [Planned Enhancements](#planned-enhancements)
3. [Technical Debt](#technical-debt)
4. [Future Considerations](#future-considerations)

---

## Active Features

### Feature: Enhanced Network Configuration

**Status**: Planned
**Priority**: High
**Target Release**: 4.2.0

**Description**:
Expand network configuration capabilities to support advanced networking scenarios including multi-WAN, bonding, and complex routing.

**Requirements**:
- Support network bonding/teaming
- Multi-WAN configuration with failover
- Advanced routing tables
- Bridge configuration
- VLAN tagging improvements

**Technical Approach**:
1. Extend nmcli integration in Coda binary
2. Add configuration validation in hooks
3. Add E2E tests for network scenarios
4. Document in EdgeIQ platform docs

**Dependencies**:
- NetworkManager 1.30+
- Network-control interface connected
- Coda binary update required

**Testing Plan**:
- Unit tests for configuration parsing
- E2E tests with virtual network interfaces
- Manual testing on physical hardware with multiple NICs

**Related Interfaces**:
- `network-control`
- `network-manager`
- `network-setup-control`

---

### Feature: ModemManager Integration

**Status**: In Progress
**Priority**: High
**Target Release**: 4.1.5

**Description**:
Complete cellular modem support using ModemManager for 4G/5G connectivity.

**Current State**:
- Interface declared in snap: `modem-manager`, `ppp`
- Not yet fully implemented in Coda binary
- README notes: "reserved but not supported"

**Requirements**:
- Detect and configure cellular modems
- Support multiple carriers and APNs
- Handle SIM card detection and PIN unlock
- Monitor signal strength and data usage
- Automatic failover to cellular

**Technical Approach**:
1. Integrate ModemManager D-Bus API in Coda
2. Add modem configuration to bootstrap.json
3. Implement connection management logic
4. Add monitoring and telemetry

**Testing Plan**:
- E2E tests with simulated modem (if possible)
- Manual testing with physical cellular modem
- Test with multiple carrier SIM cards
- Failover testing (Ethernet → Cellular)

**Related Interfaces**:
- `modem-manager`
- `ppp`
- `network-manager`

---

### Feature: Improved Hook Management

**Status**: Planned
**Priority**: Medium
**Target Release**: 4.2.0

**Description**:
Enhance hook system with better error handling, rollback capabilities, and validation.

**Requirements**:
- Configuration validation before applying changes
- Rollback on configuration errors
- Better error messages for users
- Hook execution logging improvements
- Configuration backup/restore

**Technical Approach**:
1. Add JSON schema validation for configuration files
2. Implement configuration backup in configure hook
3. Add rollback mechanism on validation failure
4. Enhance error messages with actionable guidance
5. Add hook execution metrics

**Testing Plan**:
- E2E tests for invalid configuration scenarios
- Hook tests with edge cases
- Rollback testing

**Related Files**:
- `snap/hooks/configure`
- `snap/hooks/install`
- `utils/shared/hook_utils.py`

---

### Feature: Better Logging and Diagnostics

**Status**: Planned
**Priority**: Medium
**Target Release**: 4.1.5

**Description**:
Improve logging, diagnostics, and troubleshooting capabilities for snap operations.

**Requirements**:
- Structured logging with levels (DEBUG, INFO, WARN, ERROR)
- Log rotation and retention policies
- Diagnostic information collection
- Health check endpoint
- Performance metrics

**Technical Approach**:
1. Standardize logging format (JSON structured logs)
2. Add log rotation configuration
3. Create diagnostic data collection script
4. Implement health check command
5. Add performance monitoring

**Testing Plan**:
- Verify log levels work correctly
- Test log rotation
- Validate diagnostic data collection
- Performance benchmark

**Related Components**:
- Hook logging (already uses Python logging)
- Coda binary logging
- Systemd journal integration

---

## Planned Enhancements

### Enhancement: Configuration Templating

**Priority**: Low
**Target Release**: 4.3.0

**Description**:
Support configuration templates for common deployment scenarios.

**Requirements**:
- Pre-defined configuration templates (production, staging, development)
- Template variable substitution
- Easy template selection via snap configuration

**Example**:
```bash
# Apply production template
sudo snap set coda config-template=production

# Custom variables
sudo snap set coda config-template=production company-id=acme
```

**Benefits**:
- Faster device provisioning
- Reduced configuration errors
- Consistent deployments

---

### Enhancement: Snap Interface Auto-Connection

**Priority**: Medium
**Target Release**: 4.2.0

**Description**:
Request auto-connection for common interfaces to reduce manual setup.

**Requirements**:
- Submit snap declaration to Snap Store
- Justify interface usage in declaration
- Request auto-connection for:
  - `network` ✓ (already auto-connected)
  - `network-bind` ✓ (already auto-connected)
  - `hardware-observe` (low risk)
  - `system-observe` (low risk)
  - `network-observe` (low risk)

**Process**:
1. Create snap declaration request
2. Provide justification for each interface
3. Submit to Snap Store forum
4. Wait for review approval

**Benefits**:
- Improved user experience
- Reduced installation steps
- Fewer support requests

---

### Enhancement: Multi-Version Testing

**Priority**: Low
**Target Release**: 4.3.0

**Description**:
Test snap updates and downgrades in E2E suite.

**Requirements**:
- Install older version
- Upgrade to newer version
- Verify data persistence
- Test configuration migration
- Test downgrade scenarios

**Testing Scenarios**:
1. Fresh install → latest version
2. Version N → Version N+1 (upgrade)
3. Version N+1 → Version N (downgrade)
4. Multiple sequential upgrades (N → N+1 → N+2)

**Benefits**:
- Catch migration issues early
- Ensure data persistence
- Validate rollback scenarios

---

### Enhancement: Offline Installation Support

**Priority**: Low
**Target Release**: 4.3.0

**Description**:
Support snap installation in air-gapped environments.

**Requirements**:
- Bundle all dependencies in snap
- Offline configuration mode
- Manual configuration file import
- Skip MQTT connection on first boot

**Technical Approach**:
1. Add offline mode flag
2. Skip network-dependent operations in hooks
3. Allow configuration file upload
4. Document offline setup procedure

**Use Cases**:
- Secure/classified networks
- Remote sites without internet
- Factory pre-provisioning

---

## Technical Debt

### Debt: Hook Error Handling

**Priority**: High
**Impact**: Medium

**Description**:
Current hook error handling is basic. Failures may leave snap in inconsistent state.

**Issues**:
- Some errors not caught (e.g., snapctl failures)
- No rollback on partial failures
- Limited error context for users

**Proposed Fix**:
- Add comprehensive try-except blocks
- Implement transaction-like behavior
- Better error messages
- Logging improvements

**Effort**: 2-3 days

---

### Debt: Configuration Translation Complexity

**Priority**: Medium
**Impact**: Low

**Description**:
The dash/underscore translation system is confusing and error-prone.

**Issues**:
- Easy to forget translation step
- Debugging is difficult
- No validation of key names

**Proposed Fix**:
- Add configuration key validation
- Document translation system better
- Consider alternative approaches (e.g., native support in Coda)

**Effort**: 3-5 days

---

### Debt: E2E Test Coverage

**Priority**: Medium
**Impact**: Medium

**Description**:
E2E tests cover basic scenarios but miss edge cases.

**Missing Coverage**:
- Network configuration changes
- TPM authentication flow
- Snap interface connection/disconnection
- Configuration validation errors
- Multiple snap updates
- Large configuration files
- Concurrent operations

**Proposed Fix**:
- Add test cases for each missing scenario
- Create test matrix for common configurations
- Add performance/load tests

**Effort**: 5-7 days

---

### Debt: Documentation Gaps

**Priority**: Low
**Impact**: Low

**Description**:
Some advanced features lack documentation.

**Missing Documentation**:
- TPM setup step-by-step guide
- Network configuration examples
- Troubleshooting guide for common issues
- Architecture diagrams
- Configuration reference

**Proposed Fix**:
- Create comprehensive documentation set
- Add examples and tutorials
- Build troubleshooting flowcharts

**Effort**: 3-5 days

---

### Debt: Post-Refresh Hook Unused

**Priority**: Low
**Impact**: Low

**Description**:
The post-refresh hook exists but contains no logic.

**Potential Uses**:
- Database migrations
- Configuration format updates
- Cleanup of deprecated files
- Version-specific upgrade logic

**Proposed Fix**:
- Identify use cases for post-refresh
- Implement migration logic
- Add tests for upgrade scenarios

**Effort**: 1-2 days

---

## Future Considerations

### Consideration: Classic Snap Support

**Description**:
Evaluate creating a classic confinement version for easier system access.

**Pros**:
- Simpler interface management
- Full system access
- Easier debugging

**Cons**:
- Reduced security
- Snap Store may not approve
- Less isolation

**Decision**: Defer - strict confinement is preferred for security

---

### Consideration: Container Support

**Description**:
Support running Coda snap in containerized environments (Docker, Podman).

**Challenges**:
- Snapd not designed for containers
- Privilege requirements
- Systemd in containers

**Alternative**:
- Create Docker image with embedded snap
- Or native Docker image without snap

**Decision**: Defer - Ubuntu Core is primary target

---

### Consideration: Windows/macOS Support

**Description**:
Explore snap support for Windows and macOS via Multipass.

**Approach**:
- Run Ubuntu VM with Multipass
- Install snap inside VM
- Provide management CLI on host

**Challenges**:
- Complex setup
- Performance overhead
- Limited use cases

**Decision**: Defer - focus on Linux/Ubuntu Core

---

### Consideration: Snap Store Automation

**Description**:
Automate snap building and publishing via CI/CD.

**Requirements**:
- GitHub Actions or GitLab CI
- Snapcraft credentials in secrets
- Automated E2E testing
- Automated channel promotion

**Benefits**:
- Faster releases
- Consistent builds
- Reduced manual errors

**Decision**: Plan for 4.2.0 release

---

### Consideration: A/B Testing for Releases

**Description**:
Deploy new versions to subset of devices for gradual rollout.

**Approach**:
- Use Snap Store progressive release feature
- Monitor telemetry during rollout
- Auto-rollback on high error rate

**Benefits**:
- Reduced blast radius
- Early issue detection
- Safer deployments

**Decision**: Plan for 4.3.0 release

---

## Task Prioritization

### High Priority (Next Release)
1. ModemManager Integration (4.1.5)
2. Hook Error Handling (Technical Debt)
3. Improved Logging and Diagnostics (4.1.5)

### Medium Priority (Next 2 Releases)
1. Enhanced Network Configuration (4.2.0)
2. Improved Hook Management (4.2.0)
3. Snap Interface Auto-Connection (4.2.0)
4. E2E Test Coverage (Technical Debt)

### Low Priority (Future Releases)
1. Configuration Templating (4.3.0)
2. Multi-Version Testing (4.3.0)
3. Offline Installation Support (4.3.0)
4. Documentation Gaps (Technical Debt)

---

## Task Templates

### Feature Task Template

```markdown
### Feature: [Name]

**Status**: Planned | In Progress | Blocked | Complete
**Priority**: High | Medium | Low
**Target Release**: X.Y.Z

**Description**:
[What is the feature?]

**Requirements**:
- [Requirement 1]
- [Requirement 2]

**Technical Approach**:
1. [Step 1]
2. [Step 2]

**Dependencies**:
- [Dependency 1]
- [Dependency 2]

**Testing Plan**:
- [Test scenario 1]
- [Test scenario 2]

**Related Components**:
- [Component 1]
- [Component 2]
```

### Bug Task Template

```markdown
### Bug: [Name]

**Status**: Open | In Progress | Fixed | Won't Fix
**Priority**: Critical | High | Medium | Low
**Severity**: Blocker | Major | Minor
**Affected Version**: X.Y.Z

**Description**:
[What is the bug?]

**Reproduction Steps**:
1. [Step 1]
2. [Step 2]

**Expected Behavior**:
[What should happen?]

**Actual Behavior**:
[What actually happens?]

**Environment**:
- OS: Ubuntu Core 22
- Architecture: amd64
- Snap Version: X.Y.Z

**Logs**:
```
[Relevant log output]
```

**Proposed Fix**:
[How to fix it?]
```

---

## Contributing

To propose new features or report issues:

1. Check if task already exists in this document
2. Create detailed task description using templates
3. Discuss with team
4. Add to appropriate section
5. Update status as work progresses

---

## Summary

This task planning document provides:

- **Feature Tracking**: Planned enhancements and new capabilities
- **Technical Debt**: Known issues and improvements needed
- **Prioritization**: Clear priority levels for task planning
- **Future Considerations**: Long-term ideas for evaluation

For implementation guidance, see [../../CLAUDE.md](../../CLAUDE.md).
For technical details, see [../System/README.md](../System/README.md).
For operational procedures, see [../SOP/README.md](../SOP/README.md).

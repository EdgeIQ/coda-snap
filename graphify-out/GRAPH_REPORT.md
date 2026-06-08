# Graph Report - .  (2026-06-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 224 nodes · 280 edges · 11 communities
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ba349a0e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_EdgeIQ Symphony Platform Overview|EdgeIQ Symphony Platform Overview]]
- [[_COMMUNITY_Mock MQTTHTTP Servers (test harness)|Mock MQTT/HTTP Servers (test harness)]]
- [[_COMMUNITY_Test Environment & Dependencies|Test Environment & Dependencies]]
- [[_COMMUNITY_Snapcraft Build & InstallConfigure Hooks|Snapcraft Build & Install/Configure Hooks]]
- [[_COMMUNITY_Hook Utilities - Config Translation (codasnap)|Hook Utilities - Config Translation (coda/snap)]]
- [[_COMMUNITY_Snap Hook Tests|Snap Hook Tests]]
- [[_COMMUNITY_NetworkManager & Snapcraft Packaging|NetworkManager & Snapcraft Packaging]]
- [[_COMMUNITY_Coda Snap Concepts (Ubuntu Core)|Coda Snap Concepts (Ubuntu Core)]]
- [[_COMMUNITY_E2E Test Fixtures (Multipass)|E2E Test Fixtures (Multipass)]]
- [[_COMMUNITY_Edge Device Configuration|Edge Device Configuration]]
- [[_COMMUNITY_Snap Installation Tests|Snap Installation Tests]]

## God Nodes (most connected - your core abstractions)
1. `.agent/README.md` - 57 edges
2. `MockMQTTServer` - 10 edges
3. `Coda Snap` - 9 edges
4. `MockHTTPServer` - 7 edges
5. `EdgeIQ Coda` - 7 edges
6. `edge` - 6 edges
7. `main()` - 6 edges
8. `pytest` - 6 edges
9. `TestCodaSnapInstallation` - 5 edges
10. `generate_app_config_zip()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Get reference to the Multipass VM for test execution` --rationale_for--> `Multipass`  [EXTRACTED]
  e2e-tests/test-runner/tests/conftest.py → README.md
- `.agent/README.md` --references--> `CLAUDE.md`  [EXTRACTED]
  .agent/README.md → README.md
- `.agent/README.md` --references--> `configuration`  [EXTRACTED]
  .agent/README.md → README.md
- `.agent/README.md` --references--> `configure hook`  [EXTRACTED]
  .agent/README.md → README.md
- `.agent/README.md` --references--> `install hook`  [EXTRACTED]
  .agent/README.md → README.md

## Import Cycles
- None detected.

## Communities (11 total, 0 thin omitted)

### Community 0 - "EdgeIQ Symphony Platform Overview"
Cohesion: 0.05
Nodes (40): .agent/README.md, AppArmor, Architecture Notes, AWS IoT Core, Azure IoT Hub, BACnet, cellular, D-Bus (+32 more)

### Community 1 - "Mock MQTT/HTTP Servers (test harness)"
Cohesion: 0.10
Nodes (16): generate_app_config_zip(), main(), MockHTTPServer, MockMQTTServer, MQTT client that connects to Mosquitto broker and responds to device config requ, Handle connection to Mosquitto broker, Handle disconnection from broker, Handle incoming messages and respond with appropriate commands (+8 more)

### Community 2 - "Test Environment & Dependencies"
Cohesion: 0.10
Nodes (21): aiohttp, curl, fuse, iproute2, jq, lxd, mosquitto, mosquitto-clients (+13 more)

### Community 3 - "Snapcraft Build & Install/Configure Hooks"
Cohesion: 0.08
Nodes (23): bootstrap.company-id, bootstrap.json, bootstrap.unique-id, CLAUDE.md, conf.json, conf.mqtt.broker.host, conf.mqtt.broker.password, configure hook (+15 more)

### Community 4 - "Hook Utilities - Config Translation (coda/snap)"
Cohesion: 0.11
Nodes (21): cleanup_directory(), copy_configuration_files(), get_mac_of_first_ethernet(), get_mac_of_first_ethernet_failsafe(), load_json(), Get MAC address of first ethernet card, Copies configuration files from source directory to destination directory., Removes all files and subdirectories from the specified directory.     The dire (+13 more)

### Community 5 - "Snap Hook Tests"
Cohesion: 0.17
Nodes (11): E2E tests for Coda snap hooks (install, configure, post-refresh)  These tests, Get snap configuration value via snapctl          Args:             vm_name:, Test that install hook executes correctly on first snap installation., Test suite for Coda snap hooks (install, configure, post-refresh), Execute command in Multipass VM and return result          Args:, Test that configure hook handles basic configuration changes correctly., Test that configure hook auto-creates identifier.json when company-id and unique, Test that configure hook handles deeply nested and complex configurations. (+3 more)

### Community 6 - "NetworkManager & Snapcraft Packaging"
Cohesion: 0.12
Nodes (16): agent, edge, EDGEIQ_API_URL, EDGEIQ_CODA_SNAP_VERSION, EDGEIQ_CODA_VERSION, EDGEIQ_SNAP_NAME, https://edgeiq.atlassian.net/servicedesk/customer/portal/3, https://github.com/EdgeIQ/coda-snap.git (+8 more)

### Community 7 - "Coda Snap Concepts (Ubuntu Core)"
Cohesion: 0.15
Nodes (14): Coda Snap, configuration, device, Device Management, Edge Computing, Edge Local Service, EdgeIQ Coda, EdgeIQ Coda Snap (+6 more)

### Community 8 - "E2E Test Fixtures (Multipass)"
Cohesion: 0.14
Nodes (13): Multipass, local_snap_file(), mock_mqtt_broker(), mock_server_url(), Pytest configuration and fixtures for e2e tests, Mock server HTTP URL.     Services run inside the VM, so they're accessible via, Mock MQTT broker connection details.     Services run inside the VM, accessible, Wait for all services to be ready before running tests.     This fixture runs a (+5 more)

### Community 9 - "Edge Device Configuration"
Cohesion: 0.15
Nodes (12): device, carrier, unique_id, edge, api_url, heartbeat_interval, log_level, mqtt_broker (+4 more)

### Community 10 - "Snap Installation Tests"
Cohesion: 0.32
Nodes (5): Test suite for Coda snap installation and basic functionality, Execute command in Multipass VM and return result          Args:, Test that coda snap handles disk space exhaustion gracefully without crashing., Install the coda snap from the snap store or local file, TestCodaSnapInstallation

## Knowledge Gaps
- **87 isolated node(s):** `version`, `relay_frequency_limit`, `log_level`, `heartbeat_interval`, `api_url` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `.agent/README.md` connect `EdgeIQ Symphony Platform Overview` to `Test Environment & Dependencies`, `Snapcraft Build & Install/Configure Hooks`, `NetworkManager & Snapcraft Packaging`, `Coda Snap Concepts (Ubuntu Core)`, `E2E Test Fixtures (Multipass)`?**
  _High betweenness centrality (0.308) - this node is a cross-community bridge._
- **Why does `pytest` connect `Test Environment & Dependencies` to `EdgeIQ Symphony Platform Overview`, `E2E Test Fixtures (Multipass)`, `Snapcraft Build & Install/Configure Hooks`, `Snap Hook Tests`?**
  _High betweenness centrality (0.287) - this node is a cross-community bridge._
- **What connects `version`, `relay_frequency_limit`, `log_level` to the rest of the system?**
  _131 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `EdgeIQ Symphony Platform Overview` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Mock MQTT/HTTP Servers (test harness)` be split into smaller, more focused modules?**
  _Cohesion score 0.10461538461538461 - nodes in this community are weakly interconnected._
- **Should `Test Environment & Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.10333333333333333 - nodes in this community are weakly interconnected._
- **Should `Snapcraft Build & Install/Configure Hooks` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
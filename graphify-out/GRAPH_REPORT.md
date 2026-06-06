# Graph Report - coda-snap  (2026-06-06)

## Corpus Check
- 7 files · ~7,315 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 117 nodes · 123 edges · 8 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d84fa274`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]

## God Nodes (most connected - your core abstractions)
1. `MockMQTTServer` - 10 edges
2. `E2E Test Cases` - 10 edges
3. `E2E Testing Infrastructure` - 9 edges
4. `MockHTTPServer` - 7 edges
5. `AI Agent Instructions` - 7 edges
6. `edge` - 6 edges
7. `main()` - 6 edges
8. `Build System` - 6 edges
9. `Snap Architecture` - 6 edges
10. `Operational Protocol` - 6 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (8 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (16): generate_app_config_zip(), main(), MockHTTPServer, MockMQTTServer, MQTT client that connects to Mosquitto broker and responds to device config requ, Handle connection to Mosquitto broker, Handle disconnection from broker, Handle incoming messages and respond with appropriate commands (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (22): cleanup_directory(), copy_configuration_files(), get_mac_of_first_ethernet(), get_mac_of_first_ethernet_failsafe(), load_json(), Get MAC address of first ethernet card, Copies configuration files from source directory to destination directory., Removes all files and subdirectories from the specified directory.     The dire (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (16): Build Process Details, Build System, CI/CD, Common Build Commands, Environment Variables, Hook Architecture, Hook Development, Hook Utility Functions (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (12): device, carrier, unique_id, edge, api_url, heartbeat_interval, log_level, mqtt_broker (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.17
Nodes (12): 1. Clarification First, 2. Test-Driven Development, 3. Hook Development Standards, 4. Multipass-First Workflow, 5. Documentation Discipline, AI Agent Instructions, Common Snap Patterns, Core Expertise (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.20
Nodes (10): 1. `test_install_coda_snap`, 1. `test_install_hook_execution`, 2. `test_configure_hook_basic_config`, 2. `test_disk_space_exhaustion_crash`, 3. `test_configure_hook_identifier_creation`, 4. `test_configure_hook_complex_nested_config`, 5. `test_post_refresh_hook_cleanup`, E2E Test Cases (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.25
Nodes (8): Debugging Failed Tests, E2E Test Configuration, E2E Testing Infrastructure, Running E2E Tests, Service Architecture, Test Components, Test Environment, Testing with Local Snap Files

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (6): Apps and Services, Configuration Model, Hook Utilities, Snap Architecture, Snap Hooks, Snap Plugs

## Knowledge Gaps
- **53 isolated node(s):** `version`, `relay_frequency_limit`, `log_level`, `heartbeat_interval`, `api_url` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `E2E Testing Infrastructure` connect `Community 6` to `Community 2`, `Community 5`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `AI Agent Instructions` connect `Community 4` to `Community 2`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `E2E Test Cases` connect `Community 5` to `Community 6`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **What connects `version`, `relay_frequency_limit`, `log_level` to the rest of the system?**
  _76 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08994708994708994 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.09881422924901186 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
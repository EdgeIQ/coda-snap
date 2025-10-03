# Coda Snap E2E Tests

End-to-end testing infrastructure for the EdgeIQ Coda snap package using Docker containers.

## Architecture

The test environment consists of 3 containers orchestrated via docker-compose:

### 1. Ubuntu Core Container (`ubuntu-core`)
- **Base Image**: `ubuntu:24.04`
- **Purpose**: Simulates Ubuntu Core 24 environment with snapd installed
- **Privileges**: Runs in privileged mode to support snap operations and systemd
- **Configuration**: Installs and runs snapd service

### 2. Mock Server Container (`mock-server`)
- **Base Image**: `python:3.17-slim`
- **Purpose**: Simulates EdgeIQ API backend
- **Services**:
  - HTTP server (port 8080): Serves config downloads at `/api/v1/platform/configs_v3/*/*/*.zip`
  - Works with external MQTT broker for device communication
- **Implementation**: Python asyncio with aiohttp

### 3. MQTT Broker Container (`mqtt-broker`)
- **Base Image**: `eclipse-mosquitto:2.0`
- **Purpose**: Provides MQTT message broker for device communication
- **Configuration**: Allows anonymous connections, subscribes to all topics (`#`)
- **Port**: 1883

### 4. Test Runner Container (`test-runner`)
- **Base Image**: `python:3.17-slim`
- **Purpose**: Executes pytest tests against the Ubuntu Core container
- **Features**:
  - Has access to Docker socket to control containers
  - Executes bash commands inside `ubuntu-core` container via `docker exec`
  - Tests snap installation, configuration, and operation
- **Framework**: pytest with pytest-asyncio

## Directory Structure

```
e2e-tests/
├── docker-compose.yaml          # Orchestration configuration
├── README.md                    # This file
├── fixtures/                    # Test fixtures and mock data
│   ├── mosquitto.conf          # MQTT broker configuration
│   └── responses/              # Mock API response files
│       └── config.json         # Default config response
├── mock-server/                # Mock EdgeIQ API server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py               # HTTP server implementation
│   └── responses/              # Runtime response directory (mounted from fixtures)
└── test-runner/                # Test execution container
    ├── Dockerfile
    ├── requirements.txt
    └── tests/
        ├── conftest.py         # Pytest fixtures and configuration
        └── test_coda_snap.py   # Main test suite
```

## Prerequisites

- Docker and Docker Compose installed
- Sufficient disk space for container images (~2GB)
- Internet connection for downloading snap packages from store

## Usage

### Running All Tests

```bash
cd e2e-tests
docker-compose up --build --abort-on-container-exit
```

This will:
1. Build the mock-server and test-runner images
2. Start ubuntu-core, mqtt-broker, and mock-server containers
3. Wait for all services to be healthy
4. Run pytest test suite
5. Display test results
6. Exit and stop all containers

### Running Tests in Development Mode

To keep containers running for debugging:

```bash
# Start all services
docker-compose up -d --build

# Wait for services to be ready
docker-compose logs -f ubuntu-core

# Run tests manually
docker-compose run --rm test-runner

# View logs from specific containers
docker-compose logs -f ubuntu-core
docker-compose logs -f mock-server
docker-compose logs -f mqtt-broker

# Clean up
docker-compose down -v
```

### Running Specific Tests

```bash
# Run a specific test file
docker-compose run --rm test-runner pytest tests/test_coda_snap.py -v

# Run a specific test function
docker-compose run --rm test-runner pytest tests/test_coda_snap.py::TestCodaSnapInstallation::test_install_coda_snap -v

# Run with extra verbosity
docker-compose run --rm test-runner pytest -vv -s
```

### Debugging

#### Access Ubuntu Core Container Shell

```bash
docker exec -it ubuntu-core bash
```

Inside the container:
```bash
# Check snap status
snap list
snap services coda.agent
snap logs coda.agent -n=100

# Check snap configuration
snap get coda -d

# View config files
cat /var/snap/coda/common/conf/bootstrap.json
cat /var/snap/coda/common/conf/conf.json
cat /var/snap/coda/common/conf/identifier.json

# Check systemd status
systemctl status snapd
journalctl -u snap.coda.agent -n 50
```

#### Access Mock Server Logs

```bash
docker-compose logs -f mock-server
```

#### Access MQTT Broker Logs

```bash
docker-compose logs -f mqtt-broker
```

#### Test MQTT Connectivity

From your host machine:
```bash
# Subscribe to all topics
docker exec -it mqtt-broker mosquitto_sub -h localhost -t '#' -v

# Publish a test message
docker exec -it mqtt-broker mosquitto_pub -h localhost -t 'test/topic' -m 'hello'
```

## Test Suite

The test suite (`test_coda_snap.py`) verifies:

1. **`test_snapd_is_running`**: Validates snapd service is active
2. **`test_install_coda_snap`**: Installs coda snap from snap store (edge channel)
3. **`test_configure_coda_snap`**: Configures snap to use mock server endpoints
4. **`test_coda_agent_service_running`**: Verifies agent service is running
5. **`test_coda_snap_logs_available`**: Checks that snap is writing logs
6. **`test_coda_config_files_exist`**: Validates config files were created
7. **`test_verify_network_plugs_connected`**: Confirms network plugs are connected

## Configuration

### Mock Server Endpoints

- **Health Check**: `GET http://mock-server:8080/health`
- **Config Download**: `GET http://mock-server:8080/api/v1/platform/configs_v3/{carrier}/{filename}.zip`

Returns a zip file containing `config.json` from `fixtures/responses/config.json`.

### MQTT Broker

- **Host**: `mqtt-broker`
- **Port**: `1883`
- **Authentication**: Anonymous (no credentials required)
- **Topics**: Subscribes to all topics (`#`)

### Environment Variables

The following environment variables are available in `test-runner`:

- `UBUNTU_CORE_CONTAINER`: Name of Ubuntu Core container (default: `ubuntu-core`)
- `MOCK_SERVER_URL`: Mock server HTTP endpoint (default: `http://mock-server:8080`)
- `MOCK_MQTT_HOST`: MQTT broker hostname (default: `mqtt-broker`)
- `MOCK_MQTT_PORT`: MQTT broker port (default: `1883`)

## Customizing Mock Responses

To customize the config response returned by the mock server:

1. Edit `e2e-tests/fixtures/responses/config.json`
2. Rebuild and restart: `docker-compose up -d --build mock-server`

The mock server will automatically package this JSON into a zip file when responding to config download requests.

## Troubleshooting

### Ubuntu Core Container Fails to Start

**Symptom**: Container exits immediately or snapd is not running

**Solution**:
```bash
# Check logs
docker-compose logs ubuntu-core

# Ensure privileged mode and cgroup mount
# Already configured in docker-compose.yaml

# Restart
docker-compose restart ubuntu-core
```

### Snap Installation Fails

**Symptom**: `snap install coda` fails with connection errors

**Solutions**:
1. Ensure container has internet access
2. Check snap store connectivity: `docker exec ubuntu-core snap find coda`
3. Verify DNS resolution: `docker exec ubuntu-core ping -c 3 api.snapcraft.io`

### Tests Timeout Waiting for Services

**Symptom**: Tests fail with "service did not become ready"

**Solutions**:
1. Check service health: `docker-compose ps`
2. Increase timeout values in `conftest.py`
3. Check logs: `docker-compose logs -f`

### Mock Server Not Responding

**Symptom**: HTTP requests to mock server fail

**Solutions**:
1. Check server is running: `docker-compose logs mock-server`
2. Test health endpoint: `docker-compose exec test-runner curl http://mock-server:8080/health`
3. Verify network connectivity: `docker-compose exec test-runner ping mock-server`

### Permission Denied on Docker Socket

**Symptom**: Test runner cannot access Docker socket

**Solutions**:
1. Ensure Docker socket is mounted: Check `docker-compose.yaml` volumes
2. Run docker-compose with appropriate permissions
3. On Linux, add user to `docker` group: `sudo usermod -aG docker $USER`

## Cleanup

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images
docker-compose down -v --rmi all

# Clean up Docker system
docker system prune -a -f
```

## CI/CD Integration

To integrate with GitHub Actions or other CI systems:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run E2E Tests
        run: |
          cd e2e-tests
          docker-compose up --build --abort-on-container-exit --exit-code-from test-runner

      - name: Cleanup
        if: always()
        run: |
          cd e2e-tests
          docker-compose down -v
```

## Development Workflow

### Adding New Tests

1. Add test functions to `test-runner/tests/test_coda_snap.py`
2. Use fixtures from `conftest.py` for container access and service URLs
3. Use the `exec_command` helper method for running commands in containers
4. Run tests: `docker-compose run --rm test-runner pytest -v`

### Updating Mock Server Behavior

1. Modify `mock-server/server.py` to add new endpoints or change behavior
2. Update mock responses in `fixtures/responses/`
3. Rebuild: `docker-compose up -d --build mock-server`
4. Test changes: `docker-compose run --rm test-runner`

### Testing with Different Coda Versions

To test with a specific Coda version from the snap store:

Modify the install command in `test_coda_snap.py`:
```python
# Instead of --edge, use specific channel
self.exec_command(
    ubuntu_core_container,
    "snap install coda --channel=stable"  # or beta, candidate
)
```

## Known Limitations

1. **Snap Store Dependency**: Tests require internet access to install snap from store
2. **Systemd Requirement**: Ubuntu Core container requires privileged mode for systemd
3. **Build Time**: Initial setup takes ~2-3 minutes for service health checks
4. **Architecture**: Currently tests on amd64 only (container host architecture)

## Future Enhancements

- [ ] Add MQTT message verification tests
- [ ] Test snap configuration persistence across restarts
- [ ] Add performance tests for agent operations
- [ ] Test network manager integration
- [ ] Add support for testing locally-built snap packages
- [ ] Multi-architecture testing support
- [ ] Automated security scanning of snap

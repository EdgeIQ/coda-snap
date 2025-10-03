"""
Pytest configuration and fixtures for e2e tests
"""

import os
import time
import docker
import pytest
import requests


@pytest.fixture(scope="session")
def docker_client():
    """Provide Docker client for container interactions"""
    return docker.from_env()


@pytest.fixture(scope="session")
def ubuntu_core_container(docker_client):
    """Get reference to the Ubuntu Core container"""
    container_name = os.getenv('UBUNTU_CORE_CONTAINER', 'ubuntu-core')
    try:
        container = docker_client.containers.get(container_name)
        return container
    except docker.errors.NotFound:
        pytest.fail(f"Ubuntu Core container '{container_name}' not found")


@pytest.fixture(scope="session")
def mock_server_url():
    """Mock server HTTP URL"""
    return os.getenv('MOCK_SERVER_URL', 'http://mock-server:8080')


@pytest.fixture(scope="session")
def mock_mqtt_broker():
    """Mock MQTT broker connection details"""
    return {
        'host': os.getenv('MOCK_MQTT_HOST', 'mqtt-broker'),
        'port': int(os.getenv('MOCK_MQTT_PORT', '1883'))
    }


@pytest.fixture(scope="session", autouse=True)
def wait_for_services(mock_server_url, mock_mqtt_broker):
    """
    Wait for all services to be ready before running tests.
    This fixture runs automatically for all tests (autouse=True).
    """
    max_retries = 60
    retry_delay = 2

    print("\n" + "="*60)
    print("Waiting for all services to be ready...")
    print("="*60)

    # Wait for HTTP server
    print(f"\nChecking mock HTTP server at {mock_server_url}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{mock_server_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ Mock HTTP server is ready at {mock_server_url}")
                break
        except requests.exceptions.RequestException as e:
            if i < max_retries - 1:
                print(f"  Waiting for mock HTTP server... ({i + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                pytest.fail(f"Mock HTTP server did not become ready in time: {e}")

    # Wait for MQTT broker (simple TCP connection check)
    print(f"\nChecking MQTT broker at {mock_mqtt_broker['host']}:{mock_mqtt_broker['port']}...")
    import socket
    for i in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((mock_mqtt_broker['host'], mock_mqtt_broker['port']))
            sock.close()
            if result == 0:
                print(f"✓ MQTT broker is ready at {mock_mqtt_broker['host']}:{mock_mqtt_broker['port']}")
                break
        except Exception as e:
            if i < max_retries - 1:
                print(f"  Waiting for MQTT broker... ({i + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                pytest.fail(f"MQTT broker did not become ready in time: {e}")

    print("\n" + "="*60)
    print("All services are ready! Starting tests...")
    print("="*60 + "\n")

    yield

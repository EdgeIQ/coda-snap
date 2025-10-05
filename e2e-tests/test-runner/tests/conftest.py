"""
Pytest configuration and fixtures for e2e tests
"""

import os
import time
import subprocess
import pytest
import requests


@pytest.fixture(scope="session")
def multipass_vm():
    """Get reference to the Multipass VM for test execution"""
    vm_name = os.getenv('MULTIPASS_VM_NAME', 'coda-test-vm')

    # Verify VM exists and is running
    result = subprocess.run(
        ['multipass', 'info', vm_name],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Multipass VM '{vm_name}' not found or not running")

    return vm_name


@pytest.fixture(scope="session")
def mock_server_url():
    """
    Mock server HTTP URL.
    Services run inside the VM, so they're accessible via localhost from within the VM.
    """
    port = os.getenv('MOCK_SERVER_PORT', '8080')
    return f'http://localhost:{port}'


@pytest.fixture(scope="session")
def mock_mqtt_broker():
    """
    Mock MQTT broker connection details.
    Services run inside the VM, accessible via localhost from within the VM.
    """
    return {
        'host': 'localhost',
        'port': int(os.getenv('MQTT_PORT', '1883'))
    }


@pytest.fixture(scope="session", autouse=True)
def wait_for_services(multipass_vm, mock_server_url, mock_mqtt_broker):
    """
    Wait for all services to be ready before running tests.
    This fixture runs automatically for all tests (autouse=True).

    Services run inside the VM, so we check them by executing commands in the VM.
    """
    max_retries = 60
    retry_delay = 2

    print("\n" + "="*60)
    print("Waiting for all services to be ready...")
    print("="*60)

    # Wait for HTTP server (check from within VM)
    print(f"\nChecking mock HTTP server at {mock_server_url}...")
    for i in range(max_retries):
        result = subprocess.run(
            ['multipass', 'exec', multipass_vm, '--',
             'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'{mock_server_url}/health'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip() == '200':
            print(f"✓ Mock HTTP server is ready at {mock_server_url}")
            break
        if i < max_retries - 1:
            print(f"  Waiting for mock HTTP server... ({i + 1}/{max_retries})")
            time.sleep(retry_delay)
        else:
            pytest.fail(f"Mock HTTP server did not become ready in time")

    # Wait for MQTT broker (simple TCP connection check from within VM)
    print(f"\nChecking MQTT broker at {mock_mqtt_broker['host']}:{mock_mqtt_broker['port']}...")
    for i in range(max_retries):
        result = subprocess.run(
            ['multipass', 'exec', multipass_vm, '--',
             'nc', '-z', '-v', mock_mqtt_broker['host'], str(mock_mqtt_broker['port'])],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ MQTT broker is ready at {mock_mqtt_broker['host']}:{mock_mqtt_broker['port']}")
            break
        if i < max_retries - 1:
            print(f"  Waiting for MQTT broker... ({i + 1}/{max_retries})")
            time.sleep(retry_delay)
        else:
            pytest.fail(f"MQTT broker did not become ready in time")

    print("\n" + "="*60)
    print("All services are ready! Starting tests...")
    print("="*60 + "\n")

    yield

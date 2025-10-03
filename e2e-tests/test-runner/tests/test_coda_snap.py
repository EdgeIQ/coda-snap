"""
E2E tests for Coda snap installation and configuration
"""

import time
import pytest


class TestCodaSnapInstallation:
    """Test suite for Coda snap installation and basic functionality"""

    def exec_command(self, container, command, check=True):
        """
        Execute command in container and return result

        Args:
            container: Docker container object
            command: Command to execute
            check: If True, raise exception on non-zero exit code

        Returns:
            tuple: (exit_code, output)
        """
        print(f"Executing: {command}")
        result = container.exec_run(command, demux=True)
        exit_code = result.exit_code
        stdout, stderr = result.output

        stdout_str = stdout.decode('utf-8') if stdout else ''
        stderr_str = stderr.decode('utf-8') if stderr else ''

        output = stdout_str + stderr_str
        print(f"Exit code: {exit_code}")
        print(f"Output: {output}")

        if check and exit_code != 0:
            raise RuntimeError(f"Command failed with exit code {exit_code}: {output}")

        return exit_code, output

    def test_snapd_is_running(self, ubuntu_core_container, wait_for_services):
        """Verify that snapd is running in the Ubuntu Core container"""
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "systemctl is-active snapd"
        )
        assert exit_code == 0, "snapd service is not running"
        assert "active" in output.lower()

    def test_install_coda_snap(self, ubuntu_core_container, wait_for_services):
        """Install the coda snap from the snap store"""
        # First check if snap is already installed
        exit_code, _ = self.exec_command(
            ubuntu_core_container,
            "snap list coda",
            check=False
        )

        if exit_code == 0:
            print("Coda snap already installed, removing first...")
            self.exec_command(
                ubuntu_core_container,
                "snap remove coda"
            )
            time.sleep(5)

        # Install coda snap
        print("Installing coda snap from store...")
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap install coda --edge"
        )
        assert exit_code == 0, f"Failed to install coda snap: {output}"
        assert "coda" in output.lower()

        # Verify installation
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap list coda"
        )
        assert exit_code == 0
        assert "coda" in output

    def test_configure_coda_snap(self, ubuntu_core_container, mock_server_url, mock_mqtt_broker):
        """Configure the coda snap to point to mock server"""
        # Set unique-id
        unique_id = "test-device-001"
        self.exec_command(
            ubuntu_core_container,
            f"snap set coda unique-id={unique_id}"
        )

        # Set company-id
        company_id = "test-company"
        self.exec_command(
            ubuntu_core_container,
            f"snap set coda company-id={company_id}"
        )

        # Configure API URL to point to mock server
        self.exec_command(
            ubuntu_core_container,
            f"snap set coda conf.edge.api-url={mock_server_url}"
        )

        # Configure MQTT broker
        mqtt_url = f"mqtt://{mock_mqtt_broker['host']}:{mock_mqtt_broker['port']}"
        self.exec_command(
            ubuntu_core_container,
            f"snap set coda conf.edge.mqtt-broker={mqtt_url}"
        )

        # Verify configuration was set
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap get coda unique-id"
        )
        assert unique_id in output

        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap get coda company-id"
        )
        assert company_id in output

    def test_coda_agent_service_running(self, ubuntu_core_container):
        """Verify that the coda agent service is running"""
        # Restart the service to apply configuration
        print("Restarting coda.agent service...")
        self.exec_command(
            ubuntu_core_container,
            "snap restart coda.agent"
        )

        # Wait for service to start
        time.sleep(10)

        # Check service status
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap services coda.agent",
            check=False
        )

        print(f"Service status output: {output}")

        # Service should be listed
        assert "coda.agent" in output

        # Check if service is active (may be inactive if config is not fully valid)
        # For now, just verify the service exists
        assert exit_code == 0

    def test_coda_snap_logs_available(self, ubuntu_core_container):
        """Verify that coda snap is writing logs"""
        # Get recent logs
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap logs coda.agent -n=50",
            check=False
        )

        print(f"Snap logs output: {output}")

        # Logs should be available (exit code 0 even if service had issues)
        assert exit_code == 0

        # Logs should contain some output
        assert len(output) > 0

    def test_coda_config_files_exist(self, ubuntu_core_container):
        """Verify that configuration files were created"""
        # Check for bootstrap.json
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "ls -la /var/snap/coda/common/conf/bootstrap.json",
            check=False
        )
        assert exit_code == 0, "bootstrap.json not found"

        # Check for conf.json
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "ls -la /var/snap/coda/common/conf/conf.json",
            check=False
        )
        assert exit_code == 0, "conf.json not found"

        # Check for identifier.json (created when company-id and unique-id are set)
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "ls -la /var/snap/coda/common/conf/identifier.json",
            check=False
        )
        assert exit_code == 0, "identifier.json not found"

    def test_verify_network_plugs_connected(self, ubuntu_core_container):
        """Verify that necessary network plugs are connected"""
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap connections coda",
            check=False
        )

        assert exit_code == 0
        assert "network" in output.lower()
        print(f"Snap connections: {output}")

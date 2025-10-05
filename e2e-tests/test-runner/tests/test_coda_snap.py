"""
E2E tests for Coda snap installation and configuration
"""

import time
import subprocess
import pytest

MQTT_BROKER_PROTOCOL = "tcp"
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
PLATFORM_URL = "http://localhost:8080/api/v1/platform"

class TestCodaSnapInstallation:
    """Test suite for Coda snap installation and basic functionality"""

    def exec_command(self, vm_name, command, check=True, timeout=300):
        """
        Execute command in Multipass VM and return result

        Args:
            vm_name: Name of the Multipass VM
            command: Command to execute
            check: If True, raise exception on non-zero exit code
            timeout: Command timeout in seconds (default: 300)

        Returns:
            tuple: (exit_code, output)
        """
        print(f"Executing: {command}")
        try:
            result = subprocess.run(
                ['multipass', 'exec', vm_name, '--', 'bash', '-c', command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            exit_code = result.returncode
            output = result.stdout + result.stderr

            print(f"Exit code: {exit_code}")
            print(f"Output: {output}")

            if check and exit_code != 0:
                raise RuntimeError(f"Command failed with exit code {exit_code}: {output}")

            return exit_code, output
        except subprocess.TimeoutExpired:
            print(f"Command timed out after {timeout} seconds")
            raise
        except Exception as e:
            print(f"Command execution failed: {e}")
            raise

    def test_install_coda_snap(self, multipass_vm, wait_for_services):
        """Install the coda snap from the snap store"""
        
        SNAP_VERSION = "stable"
        COMPANY_ID = "test-company-001"
        UNIQUE_ID = "test-device-001"
        # Verify snapd is responsive
        print("Verifying snapd is ready...")
        for attempt in range(10):
            exit_code, _ = self.exec_command(
                multipass_vm,
                "snap version",
                check=False
            )
            if exit_code == 0:
                print("✓ snapd is ready")
                break
            print(f"Waiting for snapd (attempt {attempt + 1}/10)...")
            time.sleep(3)

        assert exit_code == 0, "Snapd did not become ready"

        # List installed snaps
        exit_code, output = self.exec_command(
            multipass_vm,
            "snap list"
        )
        print(f"Installed snaps: {output}")

        # Get info from the store about coda snap
        exit_code, output = self.exec_command(
            multipass_vm,
            "snap info coda"
        )
        print(f"Coda snap info: {output}")

        # Install coda snap version 4.1.0
        print(f"Installing coda snap version {SNAP_VERSION} from store...")
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap install coda --channel={SNAP_VERSION}",
            timeout=120
        )

        # If installation appears stuck or failed, check snap changes
        if exit_code != 0:
            print("Installation failed, checking snap changes...")
            _, changes_output = self.exec_command(
                multipass_vm,
                "snap changes",
                check=False
            )
            print(f"Snap changes: {changes_output}")

            # Try to get detailed logs
            _, log_output = self.exec_command(
                multipass_vm,
                "snap tasks --last=install",
                check=False
            )
            print(f"Snap task details: {log_output}")

        assert exit_code == 0, f"Failed to install coda snap: {output}"
        assert "coda" in output.lower()

        # Verify installation
        exit_code, output = self.exec_command(
            multipass_vm,
            "snap list"
        )
        assert exit_code == 0
        assert "coda" in output

        print("✓ Coda snap installed successfully")

        # Connect required interfaces
        print("Connecting required snap interfaces...")
        interfaces = [
            "home",
            "shutdown",
            "snapd-control",
            "hardware-observe",
            "system-observe",
            "network",
            "network-bind",
            "network-control",
            "network-manager",
            "network-manager-observe",
            "network-observe",
            "network-setup-control",
            "network-setup-observe",
            "network-status",
            "modem-manager",
            "ppp",
            "firewall-control",
            "tpm",
            "log-observe",
            "physical-memory-observe",
            "mount-observe",
            "ssh-public-keys",
            "raw-usb"
        ]

        for interface in interfaces:
            print(f"Connecting interface: {interface}")
            exit_code, output = self.exec_command(
                multipass_vm,
                f"sudo snap connect coda:{interface} :{interface}",
                check=False
            )
            if exit_code == 0:
                print(f"✓ Connected {interface}")
            else:
                print(f"⚠ Could not connect {interface}: {output}")

        print("✓ Interface connections completed")

        # Configure coda with unique-id and company-id
        print("Configuring coda snap...")
        
        # Set unique-id
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda bootstrap.unique-id={UNIQUE_ID}"
        )
        assert exit_code == 0, f"Failed to set unique-id: {output}"
        print(f"✓ Set bootstrap.unique-id={UNIQUE_ID}")

        # Set company-id
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda bootstrap.company-id={COMPANY_ID}"
        )
        assert exit_code == 0, f"Failed to set company-id: {output}"
        print(f"✓ Set bootstrap.company-id={COMPANY_ID}")

        # Set mqtt broker host & port
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.mqtt.broker.protocol={MQTT_BROKER_PROTOCOL}"
        )
        assert exit_code == 0, f"Failed to set mqtt broker protocol: {output}"
        print(f"✓ Set conf.mqtt.broker.protocol={MQTT_BROKER_PROTOCOL}")

        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.mqtt.broker.host={MQTT_BROKER_HOST}"
        )
        assert exit_code == 0, f"Failed to set mqtt broker host: {output}"
        print(f"✓ Set conf.mqtt.broker.host={MQTT_BROKER_HOST}")

        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.mqtt.broker.port={MQTT_BROKER_PORT}"
        )
        assert exit_code == 0, f"Failed to set mqtt broker port: {output}"
        print(f"✓ Set conf.mqtt.broker.port={MQTT_BROKER_PORT}")

        # Set platform url
        exit_code, output = self.exec_command(
            multipass_vm,
            f"sudo snap set coda conf.platform.url={PLATFORM_URL}"
        )
        assert exit_code == 0, f"Failed to set platform url: {output}"
        print(f"✓ Set conf.platform.url={PLATFORM_URL}")

        # Restart coda snap to apply configuration
        print("Restarting coda snap...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap restart coda"
        )
        assert exit_code == 0, f"Failed to restart coda snap: {output}"
        print("✓ Coda snap restarted")

        # Verify configuration
        print("Verifying configuration...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap get coda bootstrap"
        )
        assert exit_code == 0, f"Failed to get configuration: {output}"
        print(f"Bootstrap configuration: {output}")
        assert UNIQUE_ID in output, "unique-id not found in configuration"
        assert COMPANY_ID in output, "company-id not found in configuration"

        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap get coda conf"
        )
        assert exit_code == 0, f"Failed to get configuration: {output}"
        print(f"Configuration: {output}")
        assert MQTT_BROKER_PROTOCOL in output, "mqtt broker protocol not found in configuration"
        assert MQTT_BROKER_HOST in output, "mqtt broker host not found in configuration"
        assert f"{MQTT_BROKER_PORT}" in output, "mqtt broker port not found in configuration"
        assert PLATFORM_URL in output, "platform url not found in configuration"

        print("✓ Coda snap configured successfully")

        # Print coda snap logs
        print("Printing coda snap logs...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap logs coda"
        )
        print(f"Coda snap logs: {output}")
        assert exit_code == 0, f"Failed to get logs: {output}"

"""
E2E tests for Coda snap installation and configuration
"""

import time
import subprocess
import pytest


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
        # Wait for snap environment to be ready
        print("Waiting for snap environment to be ready...")
        time.sleep(10)

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

        # Try to install hello-world snap first (simple test)
        print("Installing hello-world snap as connectivity test...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap install hello-world"
        )
        print(f"Hello-world installation: {output}")

        # List installed snaps
        exit_code, output = self.exec_command(
            multipass_vm,
            "snap list"
        )
        print(f"Installed snaps after hello-world: {output}")
        assert exit_code == 0, f"Failed to install hello-world snap: {output}"

        # Check network interfaces (for debugging)
        print("Checking network interfaces in VM...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "ip addr show",
            check=False
        )
        print(f"Network interfaces: {output}")

        # Install coda snap
        print("Installing coda snap from store...")
        exit_code, output = self.exec_command(
            multipass_vm,
            "sudo snap install coda",
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

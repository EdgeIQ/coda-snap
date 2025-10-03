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

    def test_install_coda_snap(self, ubuntu_core_container, wait_for_services):
        """Install the coda snap from the snap store"""
        # First check if snap is already installed
        exit_code, _ = self.exec_command(
            ubuntu_core_container,
            "snap info coda",
            check=False
        )

        # Wait for snapd to stabilize after core snap installation
        print("Waiting for snapd to stabilize...")
        time.sleep(10)

        # Verify snapd is responsive
        for attempt in range(5):
            exit_code, _ = self.exec_command(
                ubuntu_core_container,
                "snap version",
                check=False
            )
            if exit_code == 0:
                break
            print(f"Snapd not ready yet (attempt {attempt + 1}/5), waiting...")
            time.sleep(5)

        assert exit_code == 0, "Snapd did not become ready"

        # Install hello-world snap
        print("Installing hello-world snap from store...")
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap install hello-world"
        )
        assert exit_code == 0, f"Failed to install hello-world snap: {output}"
        assert "hello-world" in output.lower()

        # Verify installation
        exit_code, output = self.exec_command(
            ubuntu_core_container,
            "snap list"
        )
        assert exit_code == 0
        assert "hello-world" in output
